import re
import json
import requests
from urllib.parse import quote

class DataEnricher:
    @staticmethod
    def extrair_email(lead: dict) -> str:
        email_direto = lead.get("emails") or lead.get("email")
        if email_direto:
            if isinstance(email_direto, list) and len(email_direto) > 0:
                return email_direto[0]
            elif isinstance(email_direto, str):
                cleaned = re.sub(r'[\[\]"\']', '', email_direto).strip()
                if cleaned:
                    return cleaned.split(',')[0].strip()
        
        # Fallback de varredura em todas as propriedades de texto
        for val in lead.values():
            if isinstance(val, str) and "@" in val:
                match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', val)
                if match:
                    return match.group(0)
        return None

    @staticmethod
    def extrair_localidade(lead: dict) -> tuple:
        query_input = str(lead.get("input_id") or lead.get("input") or lead.get("query") or lead.get("keyword") or "").lower()
        cidade, estado = None, None

        match_query = re.search(r'em\s+(.+?)\s+(SP|SC|PR|RS)', query_input, re.IGNORECASE)
        if match_query:
            cidade = match_query.group(1).strip()
            estado = match_query.group(2).upper()

        if (not cidade or not estado) and lead.get("complete_address"):
            try:
                addr = lead["complete_address"]
                if isinstance(addr, str):
                    addr = json.loads(addr)
                
                if addr:
                    cidade = addr.get("city") or cidade
                    estado_raw = str(addr.get("state", "")).lower().strip()
                    
                    mapa_estados = { 
                        'paraná': 'PR', 'paranã¡': 'PR', 'parana': 'PR', 
                        'são paulo': 'SP', 'sã£o paulo': 'SP', 'sao paulo': 'SP', 
                        'santa catarina': 'SC', 'rio grande do sul': 'RS' 
                    }
                    estado = mapa_estados.get(estado_raw) or (estado_raw.upper() if len(estado_raw) == 2 else 'PR')
            except Exception:
                pass
        return cidade, estado

    @staticmethod
    def definir_segmento(lead: dict, nome_fantasia: str) -> str:
        query_input = str(lead.get("input_id") or lead.get("input") or lead.get("query") or lead.get("keyword") or "").lower()
        categoria = str(lead.get("category") or "").lower()
        titulo_lower = nome_fantasia.lower()

        if 'contabilidade' in query_input or 'contabil' in categoria or 'contabil' in titulo_lower:
            return 'contabilidade'
        elif any(x in query_input for x in ['advocacia', 'advogado']) or 'advogad' in categoria or 'advocac' in categoria or 'advogad' in titulo_lower:
            return 'advocacia'
        return 'industria'

    @staticmethod
    def extrair_telefone(lead: dict) -> str:
        whatsapp_extraido = None
        order_online = lead.get("order_online")
        if order_online:
            try:
                str_val = order_online if isinstance(order_online, str) else json.dumps(order_online)
                match = re.search(r'(?:wa\.me\/|phone=|send\?phone=)(\d+)', str_val, re.IGNORECASE)
                if match:
                    whatsapp_extraido = match.group(1)
            except Exception:
                pass
        return whatsapp_extraido or lead.get("phone")

    @staticmethod
    def buscar_cnpj_casa_dos_dados(nome_fantasia: str) -> str:
        if not nome_fantasia or nome_fantasia == 'N/A':
            return None
        try:
            busca_nome = quote(nome_fantasia)
            url = f"https://api.casadosdados.com.br/solution/cnpj/query/busca/nome/{busca_nome}"
            response = requests.get(url, headers={'Accept': 'application/json'}, timeout=5)
            if response.status_code == 200:
                data = response.json().get("data", [])
                if data and len(data) > 0:
                    return data[0].get("cnpj")
        except Exception:
            pass
        return None

    @staticmethod
    def buscar_detalhes_receita_ws(cnpj: str) -> dict:
        if not cnpj:
            return {}
        try:
            cnpj_limpo = re.sub(r'\D', '', cnpj)
            url = f"https://receitaws.com.br/v1/cnpj/{cnpj_limpo}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                dados = response.json()
                if dados.get("status") == "OK":
                    return {
                        "razao_social": dados.get("nome"),
                        "porte": dados.get("porte"),
                        "capital_social": dados.get("capital_social"),
                        "data_abertura": dados.get("abertura"),
                        "situacao_cadastral": dados.get("situacao"),
                        "natureza_juridica": dados.get("natureza_juridica"),
                        "cnae_principal": dados.get("atividade_principal", [{}])[0].get("text") if dados.get("atividade_principal") else None
                    }
        except Exception:
            pass
        return {}

    def enriquecer_registro(self, lead: dict) -> dict:
        nome_fantasia = lead.get("title") or lead.get("name") or 'N/A'
        email = self.extrair_email(lead)
        cidade, estado = self.extrair_localidade(lead)
        segmento = self.definir_segmento(lead, nome_fantasia)
        telefone_bruto = self.extrair_telefone(lead)
        
        cnpj = lead.get("cnpj")
        if not cnpj:
            cnpj = self.buscar_cnpj_casa_dos_dados(nome_fantasia)

        dados_empresa = {}
        if cnpj:
            dados_empresa = self.buscar_detalhes_receita_ws(cnpj)

        # Retorna o registro higienizado e unificado
        registro = {
            "nome_fantasia": nome_fantasia,
            "endereco_completo": lead.get("address") or '',
            "cidade": cidade or lead.get("city") or '',
            "estado": estado or lead.get("state") or '',
            "telefone_bruto": telefone_bruto,
            "site_url": lead.get("website") or lead.get("site"),
            "email": email,
            "cnpj": cnpj,
            "rating": float(lead.get("review_rating") or lead.get("rating") or 0.0),
            "reviews_count": int(lead.get("review_count") or lead.get("reviews") or 0),
            "lat": lead.get("latitude") or lead.get("lat"),
            "lon": lead.get("longitude") or lead.get("lon"),
            "segmento": segmento,
            "fonte": 'google_maps_scraper'
        }
        registro.update(dados_empresa)
        return registro
