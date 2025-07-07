# Instagram API Setup Guide

## Übersicht

Der Instagram Poster Agent ermöglicht es, Inhalte direkt von der 7 Cycles AI Anwendung auf Instagram zu posten. Dazu wird die Instagram Graph API verwendet.

## Voraussetzungen

1. **Instagram Business Account**: Sie benötigen ein Instagram Business Account
2. **Facebook Developer Account**: Zugang zur Facebook Developer Konsole
3. **Facebook Page**: Eine Facebook Page, die mit dem Instagram Business Account verknüpft ist

## Setup Schritte

### 1. Facebook App erstellen

1. Gehen Sie zu [Facebook Developers](https://developers.facebook.com/)
2. Klicken Sie auf "Create App"
3. Wählen Sie "Business" als App-Typ
4. Geben Sie einen App-Namen ein (z.B. "7Cycles Instagram Poster")
5. Geben Sie Ihre E-Mail-Adresse ein
6. Klicken Sie auf "Create App"

### 2. Instagram Basic Display API hinzufügen

1. In Ihrer App-Dashboard, klicken Sie auf "Add Product"
2. Suchen Sie "Instagram Basic Display" und klicken Sie auf "Set Up"
3. Klicken Sie auf "Create New App" für Instagram

### 3. Instagram Graph API konfigurieren

1. Gehen Sie zurück zu "Add Product"
2. Suchen Sie "Instagram Graph API" und klicken Sie auf "Set Up"
3. Dies ermöglicht das Posten von Inhalten

### 4. App Review und Permissions

Für die Produktion benötigen Sie folgende Permissions:
- `instagram_basic`
- `instagram_content_publish`
- `pages_read_engagement`
- `pages_show_list`

### 5. Access Token generieren

#### Für Entwicklung (kurzfristig):

1. Gehen Sie zu Graph API Explorer: https://developers.facebook.com/tools/explorer/
2. Wählen Sie Ihre App aus
3. Wählen Sie "User Token" 
4. Fügen Sie die benötigten Permissions hinzu
5. Klicken Sie auf "Generate Access Token"

#### Für Produktion (langfristig):

```bash
# 1. User Access Token in Long-Lived Token umwandeln
curl -i -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-user-access-token}"
curl -i -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=1955068615285489&client_secret=7dfc48157d9e90a6a496a5b5ecb96f14&fb_exchange_token=EAAbyHZBJTWvEBPErnqyFInzJb8yrnKmHYwIAGNwqCmAaIhOLMWQmGUGRZBojgi8QCWXdzhBiOnM3Or5KdlmBcuHld8kZCL4mjAZCwOyZAOZBrNNuZBm9wNep4w0Vk3u7HdIpvGprxKHq02KfWPd859ec3jOJxpYfYzP6o1LgJ5NrKTqqPTqZBldZBN9Lx4s1SI1MsHTQ6hglNmpxThQsAE2jnblHgruzMgOzYGn2yVEJQZCxFpimlvZBqqbhwOZC0wZDZD"

# 2. Page Access Token erhalten
curl -i -X GET "https://graph.facebook.com/v18.0/me/accounts?access_token={long-lived-user-access-token}"
curl -i -X GET "https://graph.facebook.com/v18.0/me/accounts?access_token=EAAbyHZBJTWvEBPCmt1yKe9AZB7P8XJIhInAyQXDYK4lCvA9KZCOKR5soO3D6vt3ygL3uro1jpjTIEve8ZCsv4jgAsrtvOMkvbWiIb60KZAhITKTAscqStnP2142sDREvlR2KqWP5iWtHrsb5muacihNW0Eq3cRadLVdMvrLzDjavy7Hq9gStm2tZC4iQQsDtH0ChYtPpZAvktwyLO53"

# 3. Instagram Business Account ID finden
curl -i -X GET "https://graph.facebook.com/v18.0/{page-id}?fields=instagram_business_account&access_token={page-access-token}"
curl -i -X GET "https://graph.facebook.com/v18.0/{page-id}?fields=instagram_business_account&access_token=EAAbyHZBJTWvEBPPgFlcHRBvnsRhdBzIw6fEosVKedEZAAIcOKWOnMKN9YAV3opmZB0XshjlYWYYXTL0DwBrl0b8ZAAtE2NOcYzgQofACWrjMP9uKwXZCj0NTsL2YZAgtZCQNMAf2u2glaAOm8pZCnYrjsikFkaEwUBHHjvZBlTEmZAHcXL1ZCv2J4ZA1y4FIOg75uGrfqcrTU7pByZCVvjRYhINTKCUZAr"
```

### 6. Umgebungsvariablen konfigurieren

Fügen Sie folgende Variablen zu Ihrer `.env` Datei hinzu:

```env
# Instagram API Configuration
INSTAGRAM_ACCESS_TOKEN=your_long_lived_page_access_token_here
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id_here
BASE_URL=http://localhost:8000

# Optional: für Webhooks
FACEBOOK_APP_SECRET=your_app_secret_here
FACEBOOK_VERIFY_TOKEN=your_custom_verify_token_here
```

## Verwendung

### 1. Direkte API Nutzung

```typescript
// Content vorbereiten
const prepareResponse = await fetch('/prepare-instagram-content', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    instagram_post_id: 'post_id_here',
    visual_post_id: 'visual_post_id_here' // optional
  })
});

// Auf Instagram posten
const postResponse = await fetch('/post-to-instagram', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    instagram_post_id: 'post_id_here',
    visual_post_id: 'visual_post_id_here', // optional
    post_type: 'feed_post' // oder 'story'
  })
});
```

### 2. Frontend Integration

Der Instagram Poster Agent ist bereits in die Instagram Posts Interface integriert:

1. Erstellen Sie einen Instagram Post mit dem Text Writer Agent
2. Optional: Erstellen Sie einen visuellen Post mit dem Visual Posts Creator
3. Klicken Sie auf den 📤 Button am Instagram Post
4. Wählen Sie die gewünschte Option:
   - Nur Text (ohne Bild)
   - Mit vorhandenem visuellen Post
   - Neuen visuellen Post erstellen

## Rate Limiting

- **Instagram Feed Posts**: Maximal 25 Posts pro Tag
- **Instagram Stories**: Maximal 5 Stories pro Tag
- **Minimum Interval**: 5 Minuten zwischen Posts (implementiert)

## Fehlerbehebung

### Häufige Fehler:

1. **"Invalid access token"**
   - Access Token ist abgelaufen
   - Access Token hat nicht die richtigen Permissions

2. **"Application does not have permission"**
   - App benötigt Instagram Content Publishing Permissions
   - App muss für Produktion genehmigt werden

3. **"Rate limit exceeded"**
   - Zu viele Anfragen in kurzer Zeit
   - Warten Sie 5+ Minuten zwischen Posts

4. **"Image URL not accessible"**
   - Das Bild muss öffentlich zugänglich sein
   - BASE_URL muss korrekt konfiguriert sein

### Debug-Informationen:

```bash
# Posting Status prüfen
curl http://localhost:8000/instagram-posting-status

# Posting History anzeigen
curl http://localhost:8000/instagram-posting-history
```

## Funktionen

### Instagram Poster Agent Features:

1. **Content Optimization**: Automatische Optimierung von Captions und Hashtags
2. **Rate Limiting**: Intelligente Verwaltung der Instagram API Limits
3. **Multi-Format Support**: Feed Posts und Stories
4. **Visual Integration**: Nahtlose Integration mit Visual Posts Creator
5. **Posting History**: Vollständige Historie aller Posts
6. **Error Handling**: Umfassende Fehlerbehandlung und -meldung

### Agent Integration:

- **Text Writer Agent**: Liefert optimierte Instagram Post Texte und Hashtags
- **Visual Posts Creator**: Erstellt Instagram-optimierte Bilder
- **AI Prompt Agent**: Generiert KI-Bilder basierend auf Post-Inhalten

## Sicherheit

1. **Access Tokens**: Niemals in Code committed oder öffentlich geteilt
2. **HTTPS Required**: Alle Webhook URLs müssen HTTPS verwenden
3. **Token Rotation**: Regelmäßige Erneuerung der Access Tokens
4. **Permissions**: Minimale erforderliche Permissions verwenden

## Support

Bei Problemen:

1. Überprüfen Sie die Instagram Graph API Dokumentation
2. Validieren Sie Ihre Access Tokens im Graph API Explorer
3. Überprüfen Sie die App Review Status im Facebook Developer Dashboard
4. Konsultieren Sie die Debug-Endpunkte für detaillierte Fehlermeldungen