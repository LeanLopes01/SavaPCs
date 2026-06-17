DietPi config partition

This FAT partition is a place for relevant configuration files to pre-configure and automate your DietPi setup.
Those files will be copied into the root filesystem on first boot, if modified, to become effective, and the partition will be removed.

Apart of editing the existing files, you can also create the following for further automation:
- Automation_Custom_PreScript.sh
- Automation_Custom_Script.sh
- unattended_pivpn.conf
- dietpi-k3s.yaml

For details, please check our documentation and dietpi.txt itself:
https://dietpi.com/docs/usage/#how-to-do-an-automatic-base-installation-at-first-boot-dietpi-automation
