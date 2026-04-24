SERVER=ubuntu@92.5.42.221
SSH_KEY=~/Downloads/ssh-key-2026-04-22.key
APP_DIR=/home/ubuntu/getmytaskbot

deploy:
	git push
	ssh -i $(SSH_KEY) $(SERVER) "cd $(APP_DIR) && git pull && sudo systemctl restart taskbot"
	@echo "✅ Задеплоено!"

logs:
	ssh -i $(SSH_KEY) $(SERVER) "sudo journalctl -u taskbot -f"

status:
	ssh -i $(SSH_KEY) $(SERVER) "sudo systemctl status taskbot"

restart:
	ssh -i $(SSH_KEY) $(SERVER) "sudo systemctl restart taskbot"

ssh:
	ssh -i $(SSH_KEY) $(SERVER)
