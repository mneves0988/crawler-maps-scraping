import time
import random
import psycopg2
from psycopg2.extras import execute_values
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

class DatabaseClient:
    def __init__(self):
        self.conn_params = {
            "host": DB_HOST,
            "port": DB_PORT,
            "database": DB_NAME,
            "user": DB_USER,
            "password": DB_PASSWORD
        }

    def formatar_para_supabase(self, lead: dict) -> dict:
        whatsapp_raw = lead.get("telefone_bruto")
        if not whatsapp_raw:
            return None  # Descarta leads sem contato telefônico

        # Formatação para E.164
        whatsapp_digits = ''.join(filter(str.isdigit, str(whatsapp_raw)))
        formatted_whatsapp = None

        if len(whatsapp_digits) in [10, 11]:
            formatted_whatsapp = f"+55{whatsapp_digits}"
        elif len(whatsapp_digits) in [12, 13] and whatsapp_digits.startswith("55"):
            formatted_whatsapp = f"+{whatsapp_digits}"

        if not formatted_whatsapp:
            return None

        # Tratamento de e-mails falsos (extensões de imagens capturadas)
        email_final = lead.get("email")
        if email_final:
            email_lower = str(email_final).lower().strip()
            if any(ext in email_lower for ext in ['.png', '.jpg', '.jpeg']) or '@' not in email_lower:
                email_final = None

        estado_sigla = str(lead.get("estado", "")).strip().upper()
        if len(estado_sigla) != 2:
            estado_sigla = "PR"

        # Garante CNPJ único temporário caso falte
        cnpj_final = lead.get("cnpj")
        if not cnpj_final:
            cnpj_final = f"TEMP_{int(time.time())}_{random.randint(1000, 9999)}"

        return {
            "cnpj": cnpj_final,
            "razao_social": lead.get("razao_social") or lead.get("nome_fantasia") or 'Razão Social não identificada',
            "nome_fantasia": lead.get("nome_fantasia") or None,
            "whatsapp": formatted_whatsapp,
            "email": email_final,
            "nome_decisor": None,
            "cidade": lead.get("cidade"),
            "estado": estado_sigla,
            "segmento": lead.get("segmento") if lead.get("segmento") in ['contabilidade', 'advocacia', 'industria'] else 'industria',
            "site_url": lead.get("site_url") or None,
            "score_icp": lead.get("score_icp") or 0,
            "status": 'queued' if lead.get("status") == 'queued' else 'new',
            "origem": 'outscraper'
        }

    def upsert_leads(self, leads: list) -> int:
        formatted_leads = []
        for lead in leads:
            fmt = self.formatar_para_supabase(lead)
            if fmt:
                formatted_leads.append(fmt)

        if not formatted_leads:
            return 0

        query = """
            INSERT INTO public.bdr_prospects (
                cnpj, razao_social, nome_fantasia, whatsapp, email, nome_decisor,
                cidade, estado, segmento, site_url, score_icp, status, origem
            ) VALUES %s
            ON CONFLICT (whatsapp) DO UPDATE SET
                cnpj = EXCLUDED.cnpj,
                razao_social = EXCLUDED.razao_social,
                nome_fantasia = EXCLUDED.nome_fantasia,
                email = EXCLUDED.email,
                cidade = EXCLUDED.cidade,
                estado = EXCLUDED.estado,
                segmento = EXCLUDED.segmento,
                site_url = EXCLUDED.site_url,
                score_icp = EXCLUDED.score_icp,
                status = EXCLUDED.status,
                origem = EXCLUDED.origem,
                updated_at = NOW();
        """

        # Extração de tuplas para inserção em lote
        values = [
            (
                l["cnpj"], l["razao_social"], l["nome_fantasia"], l["whatsapp"], l["email"], l["nome_decisor"],
                l["cidade"], l["estado"], l["segmento"], l["site_url"], l["score_icp"], l["status"], l["origem"]
            )
            for l in formatted_leads
        ]

        conn = psycopg2.connect(**self.conn_params)
        try:
            with conn.cursor() as cur:
                execute_values(cur, query, values)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return len(formatted_leads)
