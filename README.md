# 🚀 DietPi Server Builder - Instalador Autônomo

Transforme qualquer computador antigo ou notebook sucateado em um poderoso Servidor de Nuvem e Mídia, de forma **100% autônoma e à prova de leigos**. 

O **DietPi Server Builder** é um utilitário para Windows que grava e pré-configura um pendrive de instalação. Ao plugar este pendrive no PC antigo, ele formata o disco, instala o sistema e configura seus aplicativos sem que você precise apertar uma única tecla.

## ✨ O que ele instala automaticamente?
- ☁️ **Nextcloud:** Sua própria nuvem pessoal (alternativa ao Google Drive).
- 🍿 **Jellyfin:** Seu serviço de streaming de mídia (alternativa ao Netflix).
- 🛡️ **Pi-hole:** Bloqueador de anúncios em nível de rede.
- 🌐 **Tailscale:** Acesso remoto seguro de qualquer lugar do mundo.
- 📁 **Samba:** Compartilhamento de arquivos nativo no Windows.
- 📡 **Avahi (mDNS):** Acesso simplificado via endereço `.local` (sem precisar saber IPs).

---

## 📥 Como Baixar e Usar (Para Usuários)

### 1. Preparação
1. Acesse a aba [Releases](../../releases) deste repositório e baixe o arquivo `salvapcs-setup.exe `.
2. Baixe a imagem base do DietPi (**Native PC - BIOS/CSM**) no [site oficial](https://dietpi.com/#download). Extraia o arquivo até obter a imagem `.img` bruta _(opcional)_.
3. Tenha em mãos um Pendrive de pelo menos 4GB (⚠️ **Atenção:** Todos os dados dele serão apagados!).

### 2. Criando o Pendrive Autônomo
1. Execute o `salvapcs-setup.exe ` (ele pedirá permissão de Administrador para gravar no pendrive).
2. Na interface gráfica:
   * Selecione o arquivo `.img` do DietPi.
   * Selecione o seu pendrive na lista.
   * Defina uma **Senha Global** (ela será usada para o Root do sistema e para o Nextcloud).
   * Defina o **Nome do Servidor** (ex: `nuvem`, `casa`, `servidor`).
   * *(Opcional)* Insira sua Auth Key do Tailscale.
3. Clique em **GRAVAR PENDRIVE AUTÔNOMO** e aguarde a conclusão.

### 3. A Mágica (Instalando no PC Antigo)
1. Retire o pendrive criado e conecte no PC antigo.
2. Certifique-se de que o PC antigo está **conectado ao roteador por um cabo de rede**.
3. Ligue o PC antigo e dê boot pelo pendrive.
4. **Vá tomar um café.** O processo leva de 20 a 30 minutos e formata o disco principal automaticamente.
5. No seu computador principal (Windows), abra o pendrive e execute o arquivo `1_CLIQUE_AQUI_PARA_ACHAR_O_SERVIDOR.bat`. Ele funcionará como um "Radar", te avisando quando o servidor estiver pronto e abrindo o painel no seu navegador!

---

## 🛠️ Como Compilar o Projeto (Para Desenvolvedores)

O projeto foi construído em Python 3 usando `PyQt6` para a interface gráfica e `WMI` para detecção de hardware de baixo nível.

### Pré-requisitos
```bash
pip install PyQt6 WMI pyinstaller
