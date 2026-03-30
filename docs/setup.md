# LinkedIn AI Avatar Automation — Setup Guide

> **Concept**: Automatically generate AI/tech insight videos in Varun Mayya's style, render them with your avatar using HeyGen, and post them to LinkedIn daily.

---

## Architecture

```
Claude AI  ──→  Script (hook + body + CTA + caption)
                          │
                     HeyGen API  ──→  MP4 video (your avatar speaking)
                          │
                   LinkedIn API  ──→  Published post
```

---

## Prerequisites

| Service | Purpose | Cost |
|---------|---------|------|
| [Anthropic API](https://console.anthropic.com) | Script generation | Pay-per-token (~$0.01/script) |
| [HeyGen](https://app.heygen.com) | Avatar video rendering | Paid plan needed |
| [LinkedIn Developer App](https://www.linkedin.com/developers/apps) | Posting API | Free |

---

## 1. Clone & Install

```bash
git clone <this-repo>
cd namango3
pip install -r requirements.txt
```

---

## 2. Create Your HeyGen Avatar

1. Log in to [HeyGen](https://app.heygen.com)
2. Go to **Avatars → Create Avatar** — record a 2-min video of yourself talking
3. Wait for processing (~30 min)
4. Copy your **Avatar ID** from the avatar detail page
5. Go to **Voices** and pick or clone your voice — copy the **Voice ID**

---

## 3. Set Up LinkedIn API

```bash
# 1. Create app at https://www.linkedin.com/developers/apps
#    - Add products: "Sign In with LinkedIn" + "Share on LinkedIn"
#    - Set redirect URI: http://localhost:8080/callback

# 2. Copy Client ID + Secret into .env, then:
python linkedin_auth.py
# Opens browser → authorizes → prints your access token + person URN
```

---

## 4. Configure `.env`

```bash
cp .env.example .env
# Edit .env with all your credentials
```

Key settings:
- `CONTENT_NICHE` — e.g. `"AI tools, automation, and building with AI"`
- `POST_TIME_UTC` — e.g. `"09:00"` for 9 AM UTC daily
- `CREATOR_NAME` — your name, used in script persona

---

## 5. Run

```bash
# Test with a single post right now:
python scheduler.py --now

# Post with a specific topic:
python scheduler.py --topic "3 AI agents that replaced my entire team"

# Start the daily scheduler (runs forever):
python scheduler.py
```

---

## Running as a Background Service (Linux)

```bash
# Create systemd service
sudo nano /etc/systemd/system/linkedin-bot.service
```

```ini
[Unit]
Description=LinkedIn AI Avatar Automation
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/namango3
ExecStart=/usr/bin/python3 scheduler.py
Restart=on-failure
EnvironmentFile=/path/to/namango3/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable linkedin-bot
sudo systemctl start linkedin-bot
sudo journalctl -u linkedin-bot -f   # tail logs
```

---

## Customising the Content Style

Edit the prompts in `content_generator.py`:

- **`TOPIC_BRAINSTORM_PROMPT`** — controls what kinds of topics Claude picks
- **`SCRIPT_GENERATION_PROMPT`** — controls tone, length, structure

To shift from Varun Mayya style → your own, edit the system prompt description in `SCRIPT_GENERATION_PROMPT`.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `HeyGen video generation failed` | Check avatar/voice IDs; ensure plan supports API access |
| `401 Unauthorized` (LinkedIn) | Re-run `python linkedin_auth.py` — token may have expired |
| `Environment variable not set` | Ensure `.env` is filled out completely |
| Video takes > 10 min | Increase `MAX_WAIT_S` in `avatar_video.py` |
