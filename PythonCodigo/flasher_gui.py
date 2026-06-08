# -*- coding: utf-8 -*-
import os
import sys
import time
import re
import ctypes
import wmi
from pathlib import Path

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QComboBox, QFileDialog, QTextEdit, QMessageBox, QGroupBox)
from PyQt6.QtCore import QThread, pyqtSignal

# ==========================================
# FUNÇÕES DE BACKEND (SISTEMA E GRAVAÇÃO)
# ==========================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def get_usb_drives():
    """Busca os drives físicos USB no Windows usando WMI."""
    drives = []
    c = wmi.WMI()
    for drive in c.Win32_DiskDrive():
        if "USB" in drive.InterfaceType:
            drives.append({"id": drive.DeviceID, "model": drive.Model, "size": int(drive.Size) // (1024**3)})
    return drives

# ==========================================
# THREAD DE TRABALHO (Evita travar a GUI)
# ==========================================
class WorkerThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def log(self, message):
        self.log_signal.emit(message)

    def run(self):
        try:
            self.flash_image()
            self.log("\n[!] Aguardando 10 segundos para o Windows remontar a partição BOOT...")
            time.sleep(10)
            
            boot_letter = self.find_boot_partition()
            if not boot_letter:
                self.log("[-] Não foi possível achar a letra da partição de boot automaticamente.")
                self.log("[-] Desplugue e replugue o pendrive, e altere o dietpi.txt manualmente.")
                self.finished_signal.emit(False)
                return

            self.modify_dietpi_txt(boot_letter)
            self.create_custom_script(boot_letter)
            
            self.log("\n====================================================")
            self.log("[+] PROCESSO CONCLUÍDO COM SUCESSO!")
            self.log("[+] O pendrive está pronto. Plugar no PC destino e ligar.")
            self.log("====================================================")
            self.finished_signal.emit(True)

        except Exception as e:
            self.log(f"[-] Erro crítico: {str(e)}")
            self.finished_signal.emit(False)

    def flash_image(self):
        img_path = self.config['img_path']
        target_disk = self.config['target_disk']
        self.log(f"[+] Iniciando formatação e gravação em {target_disk}...")
        self.log("[+] Isso pode demorar alguns minutos. Por favor, aguarde...")
        
        buffer_size = 1024 * 1024 * 4  # 4MB buffer
        with open(img_path, 'rb') as src, open(target_disk, 'r+b') as dst:
            while True:
                chunk = src.read(buffer_size)
                if not chunk:
                    break
                dst.write(chunk)
        self.log("[+] Gravação da imagem base concluída!")

    def find_boot_partition(self):
        import string
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                test_path = Path(f"{letter}:\\dietpi.txt")
                if test_path.exists():
                    self.log(f"[+] Partição DietPi encontrada na letra {letter}:")
                    return f"{letter}:\\"
            bitmask >>= 1
        return None

    def modify_dietpi_txt(self, boot_path):
        dietpi_txt_path = Path(boot_path) / "dietpi.txt"
        self.log(f"[+] Injetando configurações extremas de automação...")
        content = dietpi_txt_path.read_text(encoding="utf-8", errors="ignore")

        # IDs: 93(Pi-hole), 114(Nextcloud), 161(Jellyfin), 193(Tailscale), 119(Avahi/mDNS), 96(Samba)
        modifications = {
            "AUTO_SETUP_AUTOMATED": "1",
            "AUTO_SETUP_ACCEPT_LICENSE": "1",
            "AUTO_SETUP_LOCALE": "pt_BR.UTF-8",
            "AUTO_SETUP_KEYBOARD_LAYOUT": "br",
            "AUTO_SETUP_TIMEZONE": "America/Sao_Paulo",
            "AUTO_SETUP_HOSTNAME": self.config.get("hostname", "meuservidor"),
            "AUTO_SETUP_GLOBAL_PASSWORD": self.config.get("password", "dietpi"),
            "AUTO_SETUP_AUTOSTART_TARGET_INDEX": "0",
            
            # Rede via DHCP (Automático)
            "AUTO_SETUP_NET_USESTATIC": "0",
            
            # Softwares listados
            "AUTO_SETUP_INSTALL_SOFTWARE_ID": "93 114 161 193 119 96",
            "AUTO_SETUP_CUSTOM_SCRIPT_EXEC": "1" if self.config.get("tailscale_key") else "0"
        }

        for key, value in modifications.items():
            pattern = rf"^({key}=).*$"
            replacement = f"\\g<1>{value}"
            if re.search(pattern, content, flags=re.MULTILINE):
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            else:
                content += f"\n{key}={value}"

        dietpi_txt_path.write_text(content, encoding="utf-8")
        
        # Gera o arquivo de instruções
        readme_path = Path(boot_path) / "LEIA-ME_INSTRUCOES.txt"
        hostname = self.config.get("hostname", "meuservidor")
        instrucoes = f"""PARABÉNS! SEU PENDRIVE DE SERVIDOR ESTÁ PRONTO.

Siga estes passos exatos para transformar seu PC antigo em um servidor:

1. Tire este pendrive do seu computador atual.
2. Espete no PC antigo (o cabo de rede conectado ao roteador precisa estar plugado nele!).
3. Ligue o PC antigo.
4. AGUARDE DE 20 A 30 MINUTOS. Ele vai formatar sozinho, baixar e instalar tudo pela internet.
5. Volte para o seu computador ou celular (que deve estar no mesmo Wi-Fi).

COMO ACESSAR SEUS APLICATIVOS (Digite isso no seu navegador):
- Nextcloud (Nuvem): http://{hostname}.local/nextcloud
- Jellyfin (Filmes): http://{hostname}.local:8096
- Pi-hole (Bloqueador): http://{hostname}.local/admin

Sua senha global para tudo é: {self.config.get("password")}

Para colocar filmes no servidor, abra o Explorador de Arquivos do Windows e digite:
\\\\{hostname}.local
"""
        readme_path.write_text(instrucoes, encoding="utf-8")
        
        # --- CRIA O RADAR PARA O WINDOWS ---
        bat_path = Path(boot_path) / "1_CLIQUE_AQUI_PARA_ACHAR_O_SERVIDOR.bat"
        bat_content = f"""@echo off
title Procurando Servidor
color 0A
echo ===============================================
echo      BUSCANDO SEU SERVIDOR NA REDE WI-FI
echo ===============================================
echo.
echo Tentando conectar com {hostname}.local...
ping -n 1 -w 2000 {hostname}.local >nul

if %errorlevel% equ 0 (
    echo.
    echo [SUCESSO] O servidor terminou de instalar e respondeu!
    echo Abrindo a sua Nuvem no navegador...
    timeout /t 3 >nul
    start http://{hostname}.local/nextcloud
) else (
    echo.
    color 0C
    echo [AGUARDE] O servidor ainda esta instalando ou reiniciando.
    echo Lembre-se que o processo inicial leva de 20 a 30 minutos. 
    echo.
    echo Feche esta janela e tente novamente daqui a pouco!
    echo.
    pause
)
"""
        # Salva em latin-1 para o CMD do Windows não quebrar os acentos
        bat_path.write_text(bat_content, encoding="latin-1", errors="replace")

        self.log("[+] Arquivos dietpi.txt, LEIA-ME e Radar (.bat) gerados com sucesso.")

    def create_custom_script(self, boot_path):
        ts_key = self.config.get("tailscale_key")
        if not ts_key:
            return

        script_path = Path(boot_path) / "Automation_Custom_Script.sh"
        script_content = f"""#!/bin/bash
exec > /var/log/dietpi_custom_setup.log 2>&1
echo "Iniciando pós-instalação customizada..."
echo "Autenticando o Tailscale..."
tailscale up --authkey={ts_key} --accept-dns=true
echo "Configuração concluída com sucesso!"
"""
        with open(script_path, "wb") as f:
            f.write(script_content.encode("utf-8").replace(b"\r\n", b"\n"))
        self.log("[+] Script de automação do Tailscale criado.")


# ==========================================
# INTERFACE GRÁFICA (PyQt6)
# ==========================================
class DietPiFlasherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DietPi Server Builder - Instalador Autônomo")
        self.resize(600, 550)
        self.img_path = ""
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 1. Seleção de Imagem e Drive
        group_hardware = QGroupBox("1. Hardware e Imagem Base")
        lay_hw = QVBoxLayout()
        
        box_img = QHBoxLayout()
        self.lbl_img = QLabel("Nenhuma imagem selecionada")
        btn_img = QPushButton("Selecionar arquivo DietPi .img")
        btn_img.clicked.connect(self.select_image)
        box_img.addWidget(btn_img)
        box_img.addWidget(self.lbl_img)
        
        box_drive = QHBoxLayout()
        box_drive.addWidget(QLabel("Pendrive Destino:"))
        self.combo_drives = QComboBox()
        self.refresh_drives()
        btn_refresh = QPushButton("Atualizar")
        btn_refresh.clicked.connect(self.refresh_drives)
        box_drive.addWidget(self.combo_drives)
        box_drive.addWidget(btn_refresh)

        lay_hw.addLayout(box_img)
        lay_hw.addLayout(box_drive)
        group_hardware.setLayout(lay_hw)
        layout.addWidget(group_hardware)

        # 2. Configurações Globais
        group_global = QGroupBox("2. Configurações de Acesso")
        lay_global = QVBoxLayout()
        
        box_pass = QHBoxLayout()
        box_pass.addWidget(QLabel("Senha Global (Root/Nextcloud):"))
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        box_pass.addWidget(self.txt_pass)
        
        box_ts = QHBoxLayout()
        box_ts.addWidget(QLabel("Tailscale Auth Key (Opcional):"))
        self.txt_ts = QLineEdit()
        box_ts.addWidget(self.txt_ts)
        
        lay_global.addLayout(box_pass)
        lay_global.addLayout(box_ts)
        group_global.setLayout(lay_global)
        layout.addWidget(group_global)

        # 3. Identificação do Servidor
        group_id = QGroupBox("3. Identificação do Servidor")
        lay_id = QVBoxLayout()
        
        box_host = QHBoxLayout()
        box_host.addWidget(QLabel("Nome do Servidor na Rede:"))
        self.txt_hostname = QLineEdit("meuservidor")
        self.txt_hostname.setToolTip("Não use espaços ou caracteres especiais. Ex: casa, nuvem, midia")
        box_host.addWidget(self.txt_hostname)
        
        lay_id.addLayout(box_host)
        group_id.setLayout(lay_id)
        layout.addWidget(group_id)

        # 4. Ação e Logs
        self.btn_start = QPushButton("GRAVAR PENDRIVE AUTÔNOMO")
        self.btn_start.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 10px;")
        self.btn_start.clicked.connect(self.start_process)
        layout.addWidget(self.btn_start)

        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        layout.addWidget(self.text_log)

    def select_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Selecione a Imagem do DietPi", "", "Arquivos de Imagem (*.img)")
        if file:
            self.img_path = file
            self.lbl_img.setText(Path(file).name)

    def refresh_drives(self):
        self.combo_drives.clear()
        drives = get_usb_drives()
        if not drives:
            self.combo_drives.addItem("Nenhum pendrive USB detectado")
            return
        for d in drives:
            self.combo_drives.addItem(f"{d['id']} - {d['model']} ({d['size']}GB)", d['id'])

    def update_log(self, message):
        self.text_log.append(message)
        scrollbar = self.text_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def process_finished(self, success):
        self.btn_start.setEnabled(True)
        if success:
            QMessageBox.information(self, "Sucesso", "Pendrive criado com sucesso!\nPronto para instalação autônoma.")
        else:
            QMessageBox.critical(self, "Erro", "Houve um erro no processo. Verifique os logs.")

    def start_process(self):
        if not self.img_path:
            QMessageBox.warning(self, "Aviso", "Selecione o arquivo .img do DietPi.")
            return
            
        target_disk = self.combo_drives.currentData()
        if not target_disk:
            QMessageBox.warning(self, "Aviso", "Selecione um pendrive válido.")
            return

        if not self.txt_pass.text():
            QMessageBox.warning(self, "Aviso", "A senha global é obrigatória para a instalação.")
            return
            
        hostname = self.txt_hostname.text().strip().replace(" ", "-").lower()
        if not hostname:
            QMessageBox.warning(self, "Aviso", "O nome do servidor é obrigatório.")
            return

        resposta = QMessageBox.question(self, "Atenção Crítica", 
                                        f"Isso irá APAGAR TODOS OS DADOS do disco {target_disk}!\nTem certeza absoluta?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if resposta == QMessageBox.StandardButton.Yes:
            self.btn_start.setEnabled(False)
            self.text_log.clear()
            
            config = {
                "img_path": self.img_path,
                "target_disk": target_disk,
                "password": self.txt_pass.text(),
                "tailscale_key": self.txt_ts.text(),
                "hostname": hostname
            }

            self.worker = WorkerThread(config)
            self.worker.log_signal.connect(self.update_log)
            self.worker.finished_signal.connect(self.process_finished)
            self.worker.start()

if __name__ == "__main__":
    if not is_admin():
        run_as_admin()
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = DietPiFlasherApp()
    window.show()
    sys.exit(app.exec())