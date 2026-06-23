import datetime
import math

def gerar_queries_do_dia() -> list:
    segmentos = [
        'escritório de contabilidade',
        'escritório de advocacia', 
        'indústria'
    ]

    cidades_por_estado = {
        'SP': ['São Paulo', 'Campinas', 'Guarulhos', 'Osasco', 'Santo André',
               'São Bernardo', 'Sorocaba', 'Ribeirão Preto', 'Santos', 'Jundiaí',
               'Piracicaba', 'Bauru', 'São José dos Campos'],
        'SC': ['Florianópolis', 'Joinville', 'Blumenau', 'Chapecó', 'Criciúma',
               'Itajaí', 'Lages', 'São José', 'Jaraguá do Sul'],
        'PR': ['Curitiba', 'Londrina', 'Maringá', 'Cascavel', 'Ponta Grossa',
               'São José dos Pinhais', 'Colombo', 'Guarapuava'],
        'RS': ['Porto Alegre', 'Caxias do Sul', 'Pelotas', 'Canoas', 'Santa Maria',
               'Gravataí', 'Viamão', 'Novo Hamburgo', 'São Leopoldo']
    }

    todas_combinacoes = []
    for estado, cidades in cidades_por_estado.items():
        for cidade in cidades:
            for segmento in segmentos:
                todas_combinacoes.append({
                    "query": f"{segmento} em {cidade} {estado}",
                    "segmento": segmento.split()[-1],
                    "cidade": cidade,
                    "estado": estado
                })

    # Seed determinístico pelo dia atual
    hoje = datetime.date.today().isoformat()
    seed = sum(ord(c) for c in hoje)

    # Shuffle determinístico (LCG)
    n = len(todas_combinacoes)
    for i in range(n - 1, 0, -1):
        seed = (seed * 9301 + 49297) % 233280
        j = math.floor((seed / 233280) * (i + 1))
        todas_combinacoes[i], todas_combinacoes[j] = todas_combinacoes[j], todas_combinacoes[i]

    # Retorna apenas as top 5 do dia
    queries_do_dia = [item["query"] for item in todas_combinacoes[:5]]
    return queries_do_dia
