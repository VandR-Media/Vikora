# Цифровая подпись Vikora (инструкция владельцу)

Сценарий: [sign-windows-azure.yml](../.github/workflows/sign-windows-azure.yml). Он **не** выполняется автоматически и пока **не** подключён к действующему сертификату.

## Важно

**Никаких готовых доверенных закрытых ключей здесь нет.** Для подписи Windows, которой доверяют другие компьютеры, требуется подтверждённый издатель и сертификат Public Trust. Самоподписанный тестовый сертификат не избавит от SmartScreen. Даже после доверенной подписи SmartScreen может предупреждать о новых релизах.

Azure Artifact Signing доступен организациям в США/Канаде/ЕС/Великобритании; индивидуальным разработчикам — сейчас в США/Канаде. Если вы физическое лицо в ЕС, используйте подходящего поставщика сертификата (часто USB-токен или облачный HSM).

## Настройка Azure Artifact Signing

1. Откройте https://portal.azure.com/ , выберите Azure Subscription.
2. Создайте Artifact Signing Account, пройдите Identity validation.
3. Создайте **Public Trust Certificate Profile** (не Private Trust).
4. В **Microsoft Entra → App registrations** создайте приложение для GitHub.
5. В **Federated credentials** добавьте GitHub Actions:
   - Owner: `VandR-Media`
   - Repository: `Vikora`
   - Entity type: Environment
   - Environment name: `release-signing`
   - Subject: `repo:VandR-Media/Vikora:environment:release-signing`
   - Audience: `api://AzureADTokenExchange`
6. Назначьте приложению Azure роль **Artifact Signing Certificate Profile Signer** на профиль.
7. В GitHub создайте Environment `release-signing` через https://github.com/VandR-Media/Vikora/settings/environments — ограничьте веткой `main` и по возможности требуйте ручное подтверждение.
8. В GitHub по адресу https://github.com/VandR-Media/Vikora/settings/secrets/actions создайте **Secrets**:

| Secret | Значение из Azure |
|---|---|
| `AZURE_CLIENT_ID` | Application (client) ID |
| `AZURE_TENANT_ID` | Directory (tenant) ID |
| `AZURE_SUBSCRIPTION_ID` | Subscription ID |

9. В том же разделе GitHub создайте **Variables**:

| Variable | Значение из Azure |
|---|---|
| `VIKORA_SIGNING_ENDPOINT` | Региональный URL вида `https://eus.codesigning.azure.net/` — точный адрес из вашего аккаунта |
| `VIKORA_SIGNING_ACCOUNT` | Artifact Signing Account name |
| `VIKORA_SIGNING_PROFILE` | Public Trust Certificate Profile name |

10. Подпись: GitHub → Actions → **Vikora — подписанный Windows-установщик Azure** → Run workflow → main.
11. Успешный артефакт должен называться `vikora-windows-signed-azure`. Сценарий проверит подпись **Vikora.exe**, пересоберёт установщик с ней и затем подпишет установщик.

**Не создавайте AZURE_CLIENT_SECRET:** сценарий использует OIDC без постоянного пароля. Не загружайте сертификат, паспортные данные или приватные ключи в репозиторий, чат и тикеты.

Если нет возможности пройти Azure Identity validation, необходимо выбрать сертификационный центр с токеном/HSM; данный workflow на такой сертификат напрямую не рассчитан.

### Проверка результата

Скачайте артефакт и в Windows откройте свойства `.exe` → вкладка «Цифровые подписи», проверьте издателя и статус. Не используйте реальные резюме до испытаний Vikora на вашем ноутбуке.

Официальные документы:
- https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options
- https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart
- https://github.com/Azure/artifact-signing-action
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
