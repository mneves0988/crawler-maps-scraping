# Pipeline de Coleta, Enriquecimento e Qualificação de Leads (BDR)

Este projeto consiste em um pipeline de engenharia de dados desenvolvido em Python para automatizar a descoberta, higienização, enriquecimento corporativo e qualificação de potenciais clientes (leads) para operações de vendas outbound (BDR/SDR).

## Funcionalidades e Etapas do Pipeline

O pipeline foi projetado para rodar de forma agendada ou sob demanda, executando as seguintes etapas sequenciais:

- Geração Determinística de Consultas: O sistema possui um algoritmo que gera 5 termos de busca por dia combinando segmentos (escritórios de contabilidade, escritórios de advocacia e indústrias) com as principais cidades dos estados de SP, SC, PR e RS. A seleção é rotacionada diariamente usando uma semente de cálculo baseada na data atual, garantindo que toda a região seja mapeada de forma homogênea sem repetir consultas no curto prazo.

- Orquestração de Scraping: O script se comunica com uma API de extração de dados do Google Maps (Google Maps Scraper). Ele inicia o lote de buscas diárias, monitora o status do processo por meio de consultas periódicas (polling) e realiza o download dos resultados brutos em formato de tabela quando finalizado.

- Higienização e Padronização de Dados:
  - Telefones: Extração e conversão de números brutos para o formato de discagem internacional padrão E.164 (ex: +5541999999999), tratando números fixos e celulares.
  - Emails: Filtro automático para descartar arquivos inválidos que o extrator de mapas possa catalogar incorretamente (como caminhos de imagens terminados em .png ou .jpg).
  - Localidade: Normalização e correção de caracteres especiais ou codificação ANSI inválida em siglas de estados e nomes de cidades.

- Enriquecimento Corporativo: Integração com APIs externas para complementar os registros que não possuem informações completas na listagem pública do Google Maps:
  - Busca de CNPJ: Consulta de nomes fantasia na API Casa dos Dados.
  - Dados da Receita Federal: Consulta do CNPJ encontrado na API ReceitaWS para extrair dados estratégicos como porte da empresa, capital social, situação cadastral, natureza jurídica e código CNAE.

- Pontuação de Perfil de Cliente Ideal (ICP): Cada lead passa por um motor de regras que calcula uma pontuação de 0 a 100 com base em critérios de perfil de cliente ideal: presença de canais de contato válidos, porte empresarial adequado, capital social ativo e relevância/avaliações no Google Maps. Leads com score igual ou maior que 60 são classificados para a fila de abordagem imediata.

- Armazenamento e Idempotência: Os leads qualificados são enviados para uma base de dados PostgreSQL hospedada no Supabase. O sistema utiliza a instrução de inserção em lote com cláusula de conflito (UPSERT) na coluna de contato telefônico, evitando a duplicidade de registros e atualizando as informações existentes se o lead for remapeado.

## Estrutura do Projeto

O código foi dividido de forma modular seguindo o princípio de responsabilidade única:

```
crawler-maps-scraping/
├── .env.example            # Exemplo de credenciais e variáveis de ambiente
├── .gitignore              # Lista de caminhos ignorados pelo controle de versão
├── requirements.txt        # Bibliotecas Python necessárias para execução
├── config.py               # Leitura e gerenciamento de configurações do sistema
├── main.py                 # Arquivo centralizador que executa o fluxo completo
├── test_db.py              # Script utilitário para teste isolado de conexão e persistência
└── pipeline/
    ├── __init__.py
    ├── generator.py        # Algoritmo de roteamento determinístico das buscas
    ├── scraper_client.py   # Gerenciamento de requisições e pooling com a API de scraping
    ├── enricher.py         # Tratamento de dados, expressões regulares e consultas a APIs de CNPJ
    ├── scoring.py          # Lógica do cálculo de ICP e definição de status
    └── database.py         # Formação de dados para o banco e instrução SQL de inserção
```

## Pré-requisitos

Para executar o pipeline localmente, é necessário ter instalado:
- Python 3.9 ou superior
- Acesso a uma instância do PostgreSQL (ou projeto Supabase)
- Endereço ativo de uma API compatível com o Google Maps Scraper

## Configuração

1. Clone o repositório para sua máquina local.
2. Copie o arquivo de exemplo para criar suas configurações locais:
   cp .env.example .env

3. Abra o arquivo .env e preencha as variáveis com suas respectivas credenciais:
- SCRAPER_API_URL: URL base do servidor de scraping.
- DB_HOST: Host de conexão do seu banco de dados PostgreSQL.
- DB_PORT: Porta de acesso ao banco de dados (padrão: 5432).
- DB_NAME: Nome do banco de dados.
- DB_USER: Usuário com permissão de escrita e atualização.
- DB_PASSWORD: Senha correspondente do usuário de acesso.

## Instalação e Execução

Instale as dependências listadas no projeto usando o gerenciador de pacotes do Python:
  pip install -r requirements.txt

Para iniciar a execução diária do pipeline, execute o arquivo principal:
  python main.py

## Testes de Integração e Persistência

Para validar se as credenciais do seu banco de dados e as validações de tipos do PostgreSQL (incluindo as constraints e tipos ENUM personalizados) estão configuradas corretamente de forma isolada do scraper de mapas, você pode executar o script utilitário de teste:

```bash
py test_db.py

