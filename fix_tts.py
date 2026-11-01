import json
with open('config.json', encoding='utf-8') as f:
    cfg = json.load(f)
cfg['text_to_voice'] = 'edge'
cfg['tts_voice_id'] = 'th-TH-PremwadeeNeural'
cfg['always_reply_voice'] = True
with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
print('OK: text_to_voice=%s, tts_voice_id=%s' % (cfg['text_to_voice'], cfg['tts_voice_id']))
