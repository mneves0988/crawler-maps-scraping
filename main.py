import time
from pipeline.generator import gerar_queries_do_dia
from pipeline.scraper_client import ScraperClient
from pipeline.enricher import DataEnricher
from pipeline.scoring import ICPScorer
from pipeline.database import DatabaseClient

def executar_pipeline():
    print("🚀 Iniciando Pipeline BDR — Google Maps Scraper...")
    
    # 1. Geração de queries
    queries = gerar_queries_do_dia()
    print(f"📍 Queries geradas para hoje: {queries}")

    # 2. Inicia o Job no Scraper
    scraper = ScraperClient()
    job_id = scraper.criar_job(queries)
    print(f"⚙️ Job criado com ID: {job_id}. Aguardando conclusão...")

    # 3. Monitora a conclusão do Job (Pooling)
    # Aguarda intervalos antes de consultar
    while True:
        status = scraper.checar_status(job_id)
        print(f"⏱️ Status do Job: {status}")
        if status in ["ok", "completed", "success"]: # Adapte ao status de conclusão correto da API
            break
        elif status in ["failed", "error"]:
            raise Exception("O processo de scraping falhou na origem.")
        time.sleep(120)  # Checa a cada 2 minutos como no fluxo do n8n

    # 4. Download dos resultados
    df_leads = scraper.baixar_csv(job_id)
    print(f"📥 Dados brutos baixados. Total de registros: {len(df_leads)}")

    # 5. Enriquecimento e Qualificação
    enricher = DataEnricher()
    leads_enriquecidos = []
    
    for idx, row in df_leads.iterrows():
        lead_dict = row.to_dict()
        try:
            # Enriquecer CNPJ e dados da Receita
            registro = enricher.enriquecer_registro(lead_dict)
            # Avaliar o Score ICP
            registro_com_score = ICPScorer.calcular_score_e_status(registro)
            leads_enriquecidos.append(registro_com_score)
        except Exception as e:
            print(f"⚠️ Falha ao enriquecer lead {lead_dict.get('title', 'N/A')}: {e}")

    # 6. Salvamento no Banco de Dados (Supabase)
    db = DatabaseClient()
    total_salvo = db.upsert_leads(leads_enriquecidos)

    print(f"✅ Execução Concluída!")
    print(f"📊 Total de Leads Qualificados e Processados: {total_salvo}")

if __name__ == "__main__":
    executar_pipeline()
