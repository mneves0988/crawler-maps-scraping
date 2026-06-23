class ICPScorer:
    @staticmethod
    def calcular_score_e_status(lead: dict) -> dict:
        score = 30  # Base padrão

        if lead.get("telefone_bruto"):
            score += 15
        if lead.get("email"):
            score += 10
        if lead.get("site_url"):
            score += 10
        if lead.get("cnpj"):
            score += 10
        
        # Porte da empresa
        portes_desejados = ['MICRO EMPRESA', 'EMPRESA DE PEQUENO PORTE', 'ME']
        if lead.get("porte") in portes_desejados:
            score += 15
        
        # Capital Social
        capital_social = lead.get("capital_social")
        if capital_social:
            try:
                # Converte string formatada em float caso necessário
                if isinstance(capital_social, str):
                    capital_social = float(capital_social.replace('[^\d,]', '').replace(',', '.'))
                if 50000 < capital_social < 5000000:
                    score += 10
            except Exception:
                pass
        
        # Google Reviews e Prova Social
        if lead.get("rating", 0.0) >= 4.0:
            score += 5
        if lead.get("reviews_count", 0) >= 10:
            score += 5
            
        if lead.get("endereco_completo") and len(str(lead["endereco_completo"])) > 20:
            score += 5

        score_final = min(100, max(0, score))
        status_inicial = 'queued' if score_final >= 60 else 'lead_normal'

        lead_com_score = lead.copy()
        lead_com_score["score_icp"] = score_final
        lead_com_score["status"] = status_inicial
        return lead_com_score
