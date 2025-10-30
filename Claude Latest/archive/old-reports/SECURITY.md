# Security Best Practices
**Kebabalab VAPI Ordering System**

---

## 🚨 IMMEDIATE ACTION REQUIRED

### Credential Rotation Needed

If you've previously committed credentials to version control, you **MUST** rotate them immediately:

#### 1. VAPI Credentials
1. Go to https://dashboard.vapi.ai/account
2. Navigate to API Keys section
3. **Revoke** the old API key
4. **Generate** a new API key
5. Update `.env` file with new key
6. **Never commit** `.env` to git

#### 2. Twilio Credentials (if used)
1. Go to https://console.twilio.com/
2. Navigate to API keys
3. **Rotate** Auth Token if exposed
4. Update `.env` file
5. Test SMS functionality

#### 3. Webhook URLs
- If ngrok URL was committed, it's temporary anyway (changes on restart)
- For production, use a permanent domain with HTTPS

---

## 🔒 Credential Management

### DO's ✅

1. **Use Environment Variables**
   ```bash
   # Copy template and fill in values
   cp .env.example .env
   ```

2. **Keep .env Local Only**
   ```bash
   # Verify .env is in .gitignore
   grep "\.env" .gitignore
   ```

3. **Use Secrets Management** (Production)
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - Environment variables in hosting platform

4. **Rotate Regularly**
   - Rotate API keys every 90 days
   - Rotate after team member changes
   - Rotate if suspicion of compromise

### DON'Ts ❌

1. **Never Commit Credentials**
   ```bash
   # These should NEVER be in git:
   - .env files
   - API keys in code
   - Hardcoded passwords
   - Webhook secrets in scripts
   ```

2. **Never Share Credentials**
   - Don't email API keys
   - Don't paste in Slack/Discord
   - Don't share screenshots with keys visible

3. **Never Log Credentials**
   ```python
   # BAD:
   logger.info(f"API Key: {api_key}")

   # GOOD:
   logger.info("API Key configured successfully")
   ```

---

## 🛡️ Application Security

### Input Validation

All user inputs are validated:

| Field | Validation |
|-------|-----------|
| Customer Name | Max 100 chars, alphanumeric + spaces only |
| Phone Number | Valid Australian format (+61 or 04xx) |
| Menu Items | Must exist in menu.json |
| Quantities | Integer, 1-99 range |
| Customizations | Max 200 chars, sanitized for SMS |

### SQL Injection Protection

✅ **All queries use parameterized statements:**
```python
# SAFE - Parameterized
cursor.execute('SELECT * FROM orders WHERE phone = ?', (phone,))

# UNSAFE - String interpolation (NOT USED)
cursor.execute(f'SELECT * FROM orders WHERE phone = {phone}')
```

### SMS Injection Protection

Customer names and order details are sanitized before SMS:
```python
# Removes special chars, newlines, control characters
customer_name = sanitize_for_sms(customer_name)
```

### CORS Protection

Only VAPI domains allowed:
```python
CORS(app, resources={
    r"/webhook": {
        "origins": ["https://api.vapi.ai", "https://vapi.ai"]
    }
})
```

---

## 🔐 Session Security

### Session Management

- **Session ID:** Based on phone number + call ID (isolated per call)
- **TTL:** 30 minutes (configurable)
- **Cleanup:** Automatic background cleanup
- **Max Sessions:** 1000 concurrent (configurable)

### Session Isolation

Each caller's session is isolated:
```python
# Session key format: phone_number or call_id
# No session sharing between different calls
```

---

## 🌐 Network Security

### HTTPS Only

- ✅ All external communications use HTTPS
- ✅ Webhook endpoints should be HTTPS only
- ✅ ngrok provides HTTPS tunnel for development

### Rate Limiting

Implemented to prevent abuse:
- 60 requests per minute per IP (default)
- Configurable via `RATE_LIMIT` env var

### Request Size Limits

- Max request size: 10MB (configurable)
- Prevents memory exhaustion attacks

---

## 📊 Database Security

### Connection Security

- ✅ Database file permissions: 600 (owner read/write only)
- ✅ Connection pooling prevents exhaustion
- ✅ Automatic connection cleanup

### Data Protection

| Data Type | Protection |
|-----------|-----------|
| Phone Numbers | Stored in plaintext (consider encryption) |
| Order Details | Stored in plaintext |
| Customer Names | Sanitized before storage |

**Recommendation:** Implement encryption for PII (Personally Identifiable Information)

### Backup Security

```bash
# Backups should be:
- Stored securely (restricted access)
- Encrypted if containing PII
- Retained according to policy
- Tested regularly
```

---

## 🔍 Logging & Monitoring

### Safe Logging Practices

```python
# ✅ GOOD - No sensitive data
logger.info(f"Order created successfully: {order_id}")

# ❌ BAD - Logs sensitive data
logger.info(f"Customer {name} at {phone} ordered {items}")
```

### What to Log

✅ Log these:
- Request/response status codes
- Error messages (sanitized)
- Performance metrics
- Failed authentication attempts

❌ Don't log these:
- API keys
- Auth tokens
- Full phone numbers
- Customer names in plain text

### Monitoring Alerts

Set up alerts for:
- Failed authentication (rate limiting triggered)
- Database errors
- High memory usage (session leak)
- Unusual request patterns

---

## 🚀 Deployment Security

### Production Checklist

Before deploying to production:

- [ ] All credentials in environment variables
- [ ] `.env` file not in version control
- [ ] CORS restricted to VAPI domains only
- [ ] HTTPS enabled on webhook endpoint
- [ ] Rate limiting configured
- [ ] Request size limits set
- [ ] Session cleanup enabled
- [ ] Database backups configured
- [ ] Error messages don't expose system details
- [ ] Logging configured (no sensitive data)
- [ ] Health check endpoint secured

### Environment Separation

Maintain separate environments:

| Environment | Purpose | Configuration |
|-------------|---------|---------------|
| Development | Local testing | `.env` file, ngrok |
| Staging | Pre-production testing | Environment variables |
| Production | Live system | Secrets management, monitoring |

---

## 🐛 Vulnerability Reporting

### If You Find a Security Issue

**DO:**
1. Document the issue privately
2. Estimate severity (Critical/High/Medium/Low)
3. Report to system administrator immediately
4. Don't discuss publicly until patched

**DON'T:**
1. Exploit the vulnerability
2. Share details publicly before fix
3. Access data you don't own

---

## 📋 Security Audit Checklist

### Weekly
- [ ] Review access logs
- [ ] Check for failed authentication attempts
- [ ] Verify backup integrity

### Monthly
- [ ] Review API key usage
- [ ] Check for dependency updates
- [ ] Review session usage patterns
- [ ] Test backup restoration

### Quarterly
- [ ] Rotate API keys
- [ ] Security audit of code changes
- [ ] Penetration testing
- [ ] Review access permissions

---

## 📚 Additional Resources

### Security Tools

- **Dependency Scanning:** `pip-audit` or `safety`
  ```bash
  pip install pip-audit
  pip-audit
  ```

- **Secret Scanning:** `git-secrets` or `truffleHog`
  ```bash
  # Scan for accidentally committed secrets
  trufflehog filesystem . --json
  ```

- **SAST:** `bandit` (Python security linter)
  ```bash
  pip install bandit
  bandit -r kebabalab/
  ```

### Security Standards

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- CWE Top 25: https://cwe.mitre.org/top25/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework

---

## 🆘 Incident Response

### If Credentials Are Compromised

1. **Immediate Actions** (Within 5 minutes)
   - Revoke compromised credentials
   - Generate new credentials
   - Update production environment
   - Alert team

2. **Short-term Actions** (Within 1 hour)
   - Review access logs for unauthorized use
   - Check for data exfiltration
   - Document incident
   - Notify affected parties if required

3. **Follow-up Actions** (Within 24 hours)
   - Root cause analysis
   - Implement additional controls
   - Update security procedures
   - Team training if needed

---

**Last Updated:** 2025-10-23
**Next Review:** After Phase 1 completion
**Owner:** System Administrator
