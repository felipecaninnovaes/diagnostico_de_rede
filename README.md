# Diagnóstico de Rede - Versão 2.0

Um sistema abrangente de diagnóstico de rede com arquitetura limpa, detecção automática de ISP e interface moderna.

## 🚀 Características

- **Detecção automática de ISP** (Vivo, Netflex, Oi, TIM)
- **Testes abrangentes**: Ping, Traceroute, MTR, Velocidade
- **Interface moderna** com Rich (barras de progresso, tabelas coloridas)
- **Múltiplos formatos de relatório** (JSON, texto, CSV)
- **Arquitetura limpa** com separação de responsabilidades
- **Configuração flexível** via YAML
- **Logging avançado** com cores e contexto
- **Execução assíncrona** para melhor performance

## 📋 Pré-requisitos

- Python 3.8+
- Comandos de rede: `ping`, `traceroute`, `mtr`
- `speedtest-cli` (instalado automaticamente)

### Instalação de ferramentas no Ubuntu/Debian:
```bash
sudo apt update
sudo apt install iputils-ping traceroute mtr-tiny
```

### Instalação de ferramentas no CentOS/RHEL:
```bash
sudo yum install iputils traceroute mtr
```

## 🔧 Instalação

### 1. Clone o repositório:
```bash
git clone <repository-url>
cd diagnostico_de_rede
```

### 2. Instale dependências usando Poetry (recomendado):
```bash
poetry install
```

### 3. Ou usando pip:
```bash
pip install -r requirements.txt
```

## 📖 Uso

### Uso Básico
```bash
# Executa com targets padrão
python main.py

# Testa targets específicos
python main.py -t 8.8.8.8 1.1.1.1 google.com

# Carrega targets de arquivo
python main.py -f targets.txt

# Mostra apenas resumo
python main.py --summary-only
```

### Geração de Relatórios
```bash
# Gera todos os formatos de relatório
python main.py --generate-reports

# Gera apenas relatório JSON
python main.py --generate-reports --format json

# Define diretório de saída
python main.py --generate-reports --output-dir ./my-reports
```

### Configuração e Debug
```bash
# Usa arquivo de configuração personalizado
python main.py --config my-config.yaml

# Ativa debug
python main.py --log-level DEBUG

# Desabilita cores
python main.py --no-color
```

## 📁 Estrutura do Projeto

```
diagnostico_de_rede/
├── src/
│   ├── models/           # Modelos de dados
│   │   ├── network_test.py
│   │   ├── isp_info.py
│   │   └── test_results.py
│   ├── services/         # Lógica de negócio
│   │   ├── network_test_service.py
│   │   ├── isp_detector.py
│   │   └── report_service.py
│   ├── parsers/          # Parsers de saída
│   │   ├── ping_parser.py
│   │   ├── traceroute_parser.py
│   │   └── mtr_parser.py
│   ├── presenters/       # Interface de usuário
│   │   └── console_presenter.py
│   ├── config/           # Configuração
│   │   ├── config_manager.py
│   │   └── default_config.yaml
│   ├── exceptions/       # Exceções customizadas
│   │   └── network_exceptions.py
│   └── utils/            # Utilitários
│       ├── validators.py
│       └── logger.py
├── main.py               # Script principal CLI
├── requirements.txt      # Dependências
├── pyproject.toml       # Configuração Poetry
└── README.md            # Este arquivo
```

## ⚙️ Configuração

O sistema usa arquivos YAML para configuração. Por padrão, procura por:

1. `config.yaml` no diretório atual
2. `~/.network_diagnostic/config.yaml`
3. Configuração padrão incorporada

### Exemplo de arquivo de configuração:

```yaml
default_targets:
  - "8.8.8.8"
  - "1.1.1.1"
  - "208.67.222.222"

test_settings:
  ping:
    count: 4
    timeout: 10
  traceroute:
    max_hops: 30
    timeout: 5
  mtr:
    count: 10
    timeout: 60
  speed_test:
    enabled: true
    timeout: 120

report_settings:
  output_directory: "./reports"
  formats: ["json", "text", "csv"]
  auto_open: false

ui_settings:
  show_progress: true
  show_detailed_output: false
  console_width: 120
  color_theme: "auto"
```

## 📊 Relatórios

O sistema gera relatórios em múltiplos formatos:

### JSON
Formato estruturado ideal para integração com outras ferramentas.

### Texto
Relatório legível para humanos com formatação clara.

### CSV
Formato tabular para análise em planilhas.

## 🏗️ Arquitetura

O projeto segue os princípios de **Clean Architecture**:

- **Models**: Entidades de dados com validação
- **Services**: Lógica de negócio e orquestração
- **Parsers**: Processamento de saída de comandos
- **Presenters**: Interface de usuário e formatação
- **Config**: Gerenciamento de configuração
- **Utils**: Utilitários e helpers
- **Exceptions**: Tratamento de erros específicos

### Benefícios da Arquitetura:

- **Testabilidade**: Componentes isolados e testáveis
- **Manutenibilidade**: Código organizado e bem estruturado
- **Extensibilidade**: Fácil adição de novos recursos
- **Reutilização**: Componentes reutilizáveis
- **Separação de Responsabilidades**: Cada módulo tem uma função específica

## 🔍 Detecção de ISP

O sistema detecta automaticamente o provedor de internet baseado em:

- **Faixas de IP**: Padrões conhecidos de cada ISP
- **Hostname reverso**: Resolução DNS reversa
- **Múltiplas fontes**: Vários serviços de detecção de IP
- **Nível de confiança**: Indicador da qualidade da detecção

### ISPs Suportados:
- Vivo/Telefônica
- Netflex (NET Claro)
- Oi
- TIM

## 🧪 Testes

### Ping
- Latência (min/avg/max)
- Perda de pacotes
- Jitter (desvio padrão)

### Traceroute
- Rota de rede
- Número de hops
- Identificação de pontos de falha

### MTR (My Traceroute)
- Combinação de ping e traceroute
- Estatísticas por hop
- Análise de qualidade de rota

### Teste de Velocidade
- Download/Upload
- Latência do servidor
- Informações do servidor

## 📝 Logs

O sistema gera logs detalhados em:

- **Console**: Saída colorida para terminal
- **Arquivo**: Logs persistentes em `./logs/`
- **Níveis**: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## 🆚 Changelog

### v2.0.0 (Atual)
- ✅ Refatoração completa com Clean Architecture
- ✅ Execução assíncrona
- ✅ Interface modernizada com Rich
- ✅ Sistema de configuração YAML
- ✅ Logging avançado
- ✅ Múltiplos formatos de relatório
- ✅ Detecção aprimorada de ISP
- ✅ Tratamento robusto de erros

### v1.0.0 (Legado)
- ✅ Script monolítico funcional
- ✅ Detecção básica de ISP
- ✅ Testes de rede essenciais
