#!/usr/bin/env python3
"""
Ericsson IMS LI External API (X1) Mock Server
模拟 SessionService + WarrantService SOAP 响应
用于 SoapUI 客户端测试验证

使用:
  python3 /path/to/ericsson-li-mock.py

支持 SOAPAction:
  - urn:Login         → SessionService.login
  - urn:CreateWarrant  → WarrantService.createWarrant
  - urn:GetWarrantList → WarrantService.getWarrantList
  - urn:DeleteWarrant  → WarrantService.deleteWarrant
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import re

class EricssonLIMSMockHandler(BaseHTTPRequestHandler):

    responses = {
        "urn:Login": {
            "service": "SessionService",
            "response": """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ns2:loginResponse xmlns:ns2="http://session.bind.external.ws1dot8.ims.epa.ericsson.se/">
      <return>
        <status><__value>0</__value></status>
        <availableFunctions>WARRANT_SERVICE</availableFunctions>
        <availableFunctions>NE_SERVICE</availableFunctions>
        <availableFunctions>IMS_MONITOR_SERVICE</availableFunctions>
        <sessionID>SESS-ABC123XYZ-20260618</sessionID>
        <roleID>ADMIN</roleID>
        <ldapEnabled>false</ldapEnabled>
      </return>
    </ns2:loginResponse>
  </soap:Body>
</soap:Envelope>"""
        },
        "urn:CreateWarrant": {
            "service": "WarrantService",
            "response": """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ns2:createWarrantResponse xmlns:ns2="http://warrant.bind.external.ws1dot8.ims.epa.ericsson.se/">
      <return>
        <code><__value>3</__value></code>
        <reason>SUCCESS</reason>
        <objectId>10001</objectId>
      </return>
    </ns2:createWarrantResponse>
  </soap:Body>
</soap:Envelope>"""
        },
        "urn:GetWarrantList": {
            "service": "WarrantService",
            "response": """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ns2:getWarrantListResponse xmlns:ns2="http://warrant.bind.external.ws1dot8.ims.epa.ericsson.se/">
      <return>
        <response>
          <code><__value>3</__value></code>
          <reason>SUCCESS</reason>
          <objectId>10001</objectId>
        </response>
        <warrants>
          <item>
            <warrantID>10001</warrantID>
            <targetNumber>8612345678900</targetNumber>
            <targetTypeID>1</targetTypeID>
            <neName>MGW-01</neName>
            <lea>LEA_BEIJING</lea>
            <MUID>MUID-20260618-001</MUID>
            <useOneLemf>1</useOneLemf>
            <lemf>10.20.30.40:6000</lemf>
            <isTargetPABX>false</isTargetPABX>
            <legalBasis>Criminal Procedure Law Art.116</legalBasis>
            <caseID>CASE-2026-001</caseID>
            <isTargetNumberSuppressed>false</isTargetNumberSuppressed>
            <activationTime>1787011200000</activationTime>
            <terminationTime>1818547200000</terminationTime>
            <userID>admin</userID>
            <supplementaryInfo>0</supplementaryInfo>
            <GGSNMonitoring>false</GGSNMonitoring>
            <positioningPeriod>-1</positioningPeriod>
            <radiusWarrantId>-1</radiusWarrantId>
          </item>
        </warrants>
      </return>
    </ns2:getWarrantListResponse>
  </soap:Body>
</soap:Envelope>"""
        },
        "urn:DeleteWarrant": {
            "service": "WarrantService",
            "response": """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ns2:deleteWarrantResponse xmlns:ns2="http://warrant.bind.external.ws1dot8.ims.epa.ericsson.se/">
      <return>
        <code><__value>3</__value></code>
        <reason>SUCCESS</reason>
        <objectId>10001</objectId>
      </return>
    </ns2:deleteWarrantResponse>
  </soap:Body>
</soap:Envelope>"""
        }
    }

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        soap_action = self.headers.get('SOAPAction', '').strip('"')

        print(f"[EricssonLI-Mock] POST {self.path}")
        print(f"[EricssonLI-Mock] SOAPAction: {soap_action}")

        if soap_action in self.responses:
            info = self.responses[soap_action]
            print(f"[EricssonLI-Mock] --> {info['service']}: {soap_action}")

            if soap_action == "urn:CreateWarrant":
                m = re.search(r'<targetNumber>(.*?)</targetNumber>', body)
                target = m.group(1) if m else "N/A"
                m = re.search(r'<caseID>(.*?)</caseID>', body)
                case = m.group(1) if m else "N/A"
                ne_types = re.findall(r'<neType>(.*?)</neType>', body)
                print(f"[EricssonLI-Mock]  Target: {target}, Case: {case}")
                if ne_types:
                    print(f"[EricssonLI-Mock]  NE Types: {', '.join(ne_types)}")

            resp_xml = info['response'].encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/xml; charset=utf-8')
            self.send_header('Content-Length', str(len(resp_xml)))
            self.end_headers()
            self.wfile.write(resp_xml)
        else:
            print(f"[EricssonLI-Mock] ERROR: Unknown SOAPAction: {soap_action}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"<soap:Fault><faultcode>Server</faultcode><faultstring>Unknown SOAPAction</faultstring></soap:Fault>")

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    port = 19090
    server = HTTPServer(('0.0.0.0', port), EricssonLIMSMockHandler)
    print(f"[EricssonLI-Mock] Starting on port {port}")
    print(f"[EricssonLI-Mock] Endpoints:")
    print(f"  SessionService:  http://localhost:{port}/SessionServicePort")
    print(f"  WarrantService:  http://localhost:{port}/WarrantServicePort")
    print(f"[EricssonLI-Mock] Ready for X1 initialization testing...")
    server.serve_forever()
