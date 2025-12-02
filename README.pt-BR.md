# 🔄 Integração SPOT → OMIE

Sincronização automática de produtos do sistema SPOT para o ERP OMIE.

## 📖 O que é este projeto?

Este projeto é uma **integração automática** que busca produtos cadastrados no sistema SPOT e os transfere para o OMIE ERP, mantendo seu catálogo de produtos sempre atualizado.

## ✨ O que ele faz?

1. **Busca produtos do SPOT** - Conecta na API do SPOT e busca todos os produtos cadastrados
2. **Verifica duplicados** - Confere se o produto já existe no OMIE para evitar duplicações
3. **Corrige dados** - Ajusta códigos NCM incorretos automaticamente
4. **Envia para o OMIE** - Cadastra os produtos novos no OMIE
5. **Registra logs** - Mantém histórico de todas as sincronizações

## ⏰ Como funciona?

A integração roda **automaticamente a cada hora** através do GitHub Actions. Você não precisa fazer nada - ela funciona sozinha!

### Fluxo da Sincronização

```
SPOT → Busca Produtos → Verifica no OMIE → Corrige NCM → Cadastra no OMIE
```

## 🎯 Benefícios

- ✅ **Automático** - Roda sozinho a cada hora
- ✅ **Seguro** - Não duplica produtos já cadastrados
- ✅ **Inteligente** - Corrige códigos NCM inválidos
- ✅ **Rastreável** - Mantém logs de todas as operações
- ✅ **Gratuito** - Roda no GitHub Actions sem custo

## 🔧 Correções Automáticas de NCM

A integração corrige automaticamente os seguintes códigos NCM incorretos:

| NCM Incorreto | NCM Correto | Descrição |
|--------------|-------------|-----------|
| 9617.10.00   | 9025.19.90  | Termômetros e instrumentos |
| 9608.10.99   | 9608.10.00  | Canetas esferográficas |

Se novos códigos NCM incorretos forem encontrados, eles podem ser adicionados facilmente.

## 📊 O que é sincronizado?

Para cada produto do SPOT, as seguintes informações são transferidas para o OMIE:

- **Código de referência** (ProdReference)
- **Descrição** do produto (incluindo cor e código)
- **Descrição detalhada**
- **Código NCM** (corrigido, se necessário)
- **Peso bruto** (convertido de gramas para kg)
- **Unidade de medida** (UN)

## 🔍 Como acompanhar a sincronização?

### Ver logs no GitHub

1. Acesse seu repositório no GitHub
2. Clique na aba **Actions**
3. Selecione a execução mais recente
4. Clique em **Run SPOT to OMIE Sync** para ver os detalhes

### Informações nos logs

Os logs mostram:
- ✅ Quantos produtos foram buscados do SPOT
- ⏭️ Quais produtos já existiam no OMIE (ignorados)
- 🔧 Correções de NCM aplicadas
- ⚠️ Produtos que não puderam ser cadastrados (NCM não cadastrado no OMIE)
- 📬 Confirmação de produtos cadastrados com sucesso

## ⚠️ Produtos Ignorados

Alguns produtos podem ser ignorados durante a sincronização por estes motivos:

### 1. Produto já existe no OMIE
```
⏭️ Skipping 94286 — already exists in OMIE.
```
**Solução:** Nenhuma ação necessária. O produto já está cadastrado.

### 2. NCM não cadastrado no OMIE
```
⚠️ Skipping due to missing NCM: 91311
```
**Solução:** Cadastre o código NCM correspondente no OMIE antes de sincronizar novamente.

### 3. Produto sem código de referência
```
❌ Skipping product with no ProdReference
```
**Solução:** Cadastre um código de referência para o produto no SPOT.

## 🛠️ Configuração Técnica

### Credenciais Necessárias

A integração precisa de **3 credenciais** configuradas como Secrets no GitHub:

1. **SPOT_ACCESS_KEY** - Chave de acesso da API do SPOT
2. **OMIE_APP_KEY** - Chave da aplicação OMIE
3. **OMIE_APP_SECRET** - Segredo da aplicação OMIE

### Frequência de Sincronização

**Padrão:** A cada hora (no minuto 0)

Para alterar a frequência, edite o arquivo `.github/workflows/scheduled-sync.yml`:

```yaml
schedule:
  - cron: '0 * * * *'     # A cada hora
  # - cron: '0 */2 * * *' # A cada 2 horas
  # - cron: '0 9 * * *'   # Diariamente às 9h (UTC)
  # - cron: '0 9 * * 1-5' # Dias úteis às 9h (UTC)
```

⏰ **Nota:** O horário é em UTC (3 horas a frente do horário de Brasília).

## 🚀 Executar Manualmente

Se precisar executar a sincronização fora do horário programado:

1. Acesse o repositório no GitHub
2. Vá em **Actions**
3. Selecione **Scheduled SPOT to OMIE Sync**
4. Clique em **Run workflow** → **Run workflow**

## 📁 Arquivos Gerados

Durante a execução, são gerados arquivos CSV para análise:

- `produtos_spot.csv` - Todos os produtos buscados do SPOT
- `prices_spot.csv` - Preços dos produtos do SPOT
- `skipped_products.csv` - Produtos que não puderam ser cadastrados (apenas se houver)

## 💡 Dicas

### Como adicionar novos códigos NCM para correção?

Edite o arquivo `app/spot_mapper.py` e adicione no dicionário `NCM_CORRECTIONS`:

```python
NCM_CORRECTIONS = {
    "96171000": "90251990",
    "96081099": "96081000",
    "NOVO_NCM": "NCM_CORRETO",  # Adicione aqui
}
```

### Como testar localmente?

Se você tiver conhecimento técnico:

```bash
# 1. Instale as dependências
pip install -r requirements.txt

# 2. Crie um arquivo .env com suas credenciais
SPOT_ACCESS_KEY=sua-chave-spot
OMIE_APP_KEY=sua-chave-omie
OMIE_APP_SECRET=seu-secret-omie

# 3. Execute o script
python app/main.py
```

## 🆘 Suporte

### A sincronização parou de funcionar?

1. Verifique se as credenciais (Secrets) estão corretas no GitHub
2. Verifique os logs no GitHub Actions para identificar o erro
3. Confirme que as APIs do SPOT e OMIE estão funcionando

### Encontrou um produto com NCM incorreto?

Abra uma issue no repositório ou edite diretamente o arquivo `app/spot_mapper.py` adicionando a correção.

### Precisa de ajuda?

Entre em contato com o responsável técnico do projeto ou abra uma issue no GitHub.

## 📝 Notas Importantes

- ⚠️ A integração **não atualiza** produtos existentes, apenas cadastra novos
- ⚠️ A integração **não deleta** produtos do OMIE
- ⚠️ Produtos sem código de referência no SPOT são ignorados
- ⚠️ O GitHub Actions pode ter um atraso de 3-10 minutos nas execuções programadas em horários de pico

## 🏗️ Tecnologias Utilizadas

- **Python 3.11** - Linguagem de programação
- **GitHub Actions** - Automação e agendamento
- **SPOT API** - Busca de produtos
- **OMIE API** - Cadastro de produtos

---

✨ **Integração desenvolvida para manter seu catálogo OMIE sempre atualizado com os produtos do SPOT, de forma automática e segura.**

