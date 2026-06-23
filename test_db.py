import os
from dotenv import load_dotenv
from pipeline.database import DatabaseClient

# Carrega as credenciais do seu arquivo .env ajustado
load_dotenv()

def testar_upsert_isolado():
    print("Iniciando teste de conexao e UPSERT no Supabase...")
    print(f"Host de conexao ativo: {os.getenv('DB_HOST')}")
    
    # Criamos um dicionario simulando o retorno do pipeline enriquecido
    lead_simulado = {
        "cnpj": "00000000000191", 
        "razao_social": "Empresa de Teste Integrado Python LTDA",
        "nome_fantasia": "Teste Local Python",
        "telefone_bruto": "11999999999", # O formatador convertera para +5511999999999
        "email": "teste_bdr@exemplo.com.br",
        "cidade": "São Paulo",
        "estado": "SP",
        "segmento": "contabilidade", # Valor valido para o seu ENUM bdr_segmento
        "site_url": "https://teste.com.br",
        "score_icp": 85,
        "status": "new" # Valor valido para o seu ENUM bdr_status_prospect
    }
    
    db = DatabaseClient()
    
    try:
        print(f"Tentando gravar o lead de teste (WhatsApp: {lead_simulado['telefone_bruto']})...")
        total_salvo = db.upsert_leads([lead_simulado])
        print(f"Sucesso! Registros processados no banco de dados: {total_salvo}")
        print("Verifique no seu painel do Supabase se o registro de teste foi inserido ou atualizado na tabela public.bdr_prospects.")
    except Exception as e:
        print(f"Falha na execucao do UPSERT: {e}")

if __name__ == "__main__":
    testar_upsert_isolado()