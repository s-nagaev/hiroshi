<h1 align="center"><img width=150 src="https://github.com/s-nagaev/hiroshi/raw/main/docs/logo.png" alt="logo"></h1>

[![Build](https://github.com/s-nagaev/hiroshi/actions/workflows/build.yml/badge.svg)](https://github.com/s-nagaev/hiroshi/actions/workflows/build.yml)
[![docker image arch](https://img.shields.io/badge/docker%20image%20arch-amd64%20%7C%20arm64%20-informational)](https://hub.docker.com/r/pysergio/hiroshi/tags)
[![docker image size](https://img.shields.io/docker/image-size/pysergio/hiroshi/latest)](https://hub.docker.com/r/pysergio/hiroshi/tags)
![license](https://img.shields.io/github/license/s-nagaev/hiroshi)

## ⚠️ Project Archived ⚠️

**Please note:** This project, **Hiroshi**, is no longer actively maintained and has been archived.

### Reason for Archiving

Hiroshi was initially created as a solution to access Large Language Models (LLMs) like GPT-3.5 and GPT-4 via Telegram during a time when official API access was often associated with significant costs. It utilized unofficial methods (based on `gpt4free`) to provide this access freely.

However, the landscape surrounding LLM access has evolved considerably:

1.  **Rise of Free Official API Tiers:** Many providers, including Google, Cloudflare, Moonshot, and others, now offer generous free tiers for their official LLM APIs. This significantly lowers the barrier to entry for legitimate, stable access.
2.  **Reliability and Legitimacy:** Official APIs offer far greater reliability, stability, and performance compared to the unofficial methods Hiroshi relied upon. Using official channels is also the intended and more sustainable way to interact with these services.
3.  **Focus Shift to a Successor Project:** Development efforts have shifted to a more modern and robust project, **[Chibi](https://github.com/s-nagaev/chibi)**.

### Recommended Alternative: Chibi

If you are looking for a Telegram bot to interact with various LLMs, I strongly recommend checking out **[Chibi](https://github.com/s-nagaev/chibi)**.

*   **Official API Integration:** Chibi connects directly to official APIs from numerous providers.
*   **Supports Free Tiers:** It fully supports providers offering free access, allowing you to leverage those benefits.
*   **Actively Developed:** Chibi is under active development, receiving updates and new features.
*   **Reliable & Stable:** Offers a much more dependable experience due to its use of official APIs.

Essentially, **Chibi provides the same core goal as Hiroshi but achieves it through more reliable, legitimate, and sustainable means**, taking advantage of the current availability of free official APIs. Given these factors, maintaining Hiroshi is no longer practical or necessary.

Thank you to everyone who showed interest in Hiroshi during its active time! Please consider migrating to [Chibi](https://github.com/s-nagaev/chibi) for ongoing development and support.

---
## Hiroshi

Hiroshi is a [GPT4Free](https://github.com/xtekky/gpt4free)-based Telegram chatbot that offers 100% free access to 
interact with GPT-3.5, GPT-4, and Llama2 language models, inclusive of Bing, You, AI Chat, and more. Users have the 
freedom to select their preferred model or specific provider. Do note, the speed/stability may be slightly diminished 
when working with certain providers. Conversation context is fully retained when you switch between models and 
providers.

**Note:** This bot provides access to public free services. The quality and speed of such services can vary depending on 
various conditions and their current load. If you need a bot that uses the official OpenAI API and you have an API KEY, 
please check the following repository: https://github.com/s-nagaev/chibi.

## Supported platforms

- linux/amd64
- linux/arm64 *(Raspberry Pi 4+ is supported!)*

## Features

- Access to language models such as GPT-3.5, GPT-4, Llama2.
- Ability to choose a specific model or provider, with the fastest and most available provider automatically selected for the chosen model.
- Customizable storage time for conversation history.
- Preservation of conversation history even when changing providers or models.
- Pre-configured for quick setup, requiring only a Telegram bot token to get started.
- Cross-platform support (amd64, arm64).
- MIT License.

## Can I try it?

Sure! [@hiroshi_gpt_bot](https://t.me/hiroshi_gpt_bot)


## System Requirements

The application is not resource-demanding at all. It works perfectly on the minimal Raspberry Pi 4 and the cheapest AWS 
EC2 Instance `t4g.nano` (2 arm64 cores, 512MB RAM), while being able to serve many people simultaneously.

## Prerequisites

- Docker
- Docker Compose (optional)

## Getting Started

### Using Docker Run

1. Pull the Hiroshi Docker image:

    ```shell
    docker pull pysergio/hiroshi:latest
    ```

2. Run the Docker container with the necessary environment variables:

    ```shell
    docker run -d \
      -e TELEGRAM_BOT_TOKEN=<your_telegram_token> \
      -v <path_to_local_data_directory>:/app/data \
      --name hiroshi \
      pysergio/hiroshi:latest
    ```
   Replace `<your_telegram_token>` and `<path_to_local_data_directory>` with appropriate values.

### Using Docker Compose

1. Create a `docker-compose.yml` file with the following contents:

   ```yaml
      version: '3'

      services:
        hiroshi:
         restart: unless-stopped
         image: pysergio/hiroshi:latest
         environment:
           TELEGRAM_BOT_TOKEN: <your_telegram_token>
         volumes:
           - hiroshi_data:/app/data
      
      volumes:
        hiroshi_data:
   ```

   Replace `<your_telegram_token>` with appropriate values.

2. Run the Docker container:

   ```shell
   docker-compose up -d
   ```

Please, visit the [examples](examples) directory of the current repository for more examples.

## Configuration

You can configure Hiroshi using the following environment variables:

| Variable                     | Description                                                                                                                                                                        | Required | Default Value                                                                    |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|----------------------------------------------------------------------------------|
| TELEGRAM_BOT_TOKEN           | Your Telegram bot token                                                                                                                                                            | Yes      |                                                                                  |
| ALLOW_BOTS                   | Allow other bots to interact with Hiroshi                                                                                                                                          | No       | false                                                                            |
| ANSWER_DIRECT_MESSAGES_ONLY  | If True the bot in group chats will respond only to messages, containing its name (see the `BOT_NAME` setting)                                                                     | No       | true                                                                             |
| ASSISTANT_PROMPT             | Initial assistant prompt for OpenAI Client                                                                                                                                         | No       | "You're helpful and friendly assistant. Your name is Hiroshi"                    |
| BOT_NAME                     | Name of the bot                                                                                                                                                                    | No       | "Hiroshi"                                                                        |
| GROUP_ADMINS                 | Comma-separated list of usernames, i.e. `"@YourName,@YourFriendName,@YourCatName"`, that should have exclusive permissions to set provider and clear dialog history in group chats | No       |                                                                                  |
| GROUPS_WHITELIST             | Comma-separated list of whitelisted group IDs, i.e `"-799999999,-788888888"`                                                                                                       | No       |                                                                                  |
| LOG_PROMPT_DATA              | Log user's prompts and GPT answers for debugging purposes.                                                                                                                         | No       | false                                                                            |
| MAX_CONVERSATION_AGE_MINUTES | Maximum age of conversations (in minutes)                                                                                                                                          | No       | 60                                                                               |
| MAX_HISTORY_TOKENS           | Maximum number of tokens in conversation history                                                                                                                                   | No       | 1800                                                                             |
| MESSAGE_FOR_DISALLOWED_USERS | Message to show disallowed users                                                                                                                                                   | No       | "You're not allowed to interact with me, sorry. Contact my owner first, please." |
| PROXY                        | Proxy settings for your application                                                                                                                                                | No       |                                                                                  |
| REDIS                        | Redis connection string, i.e. "redis://localhost"                                                                                                                                  | No       |                                                                                  |
| REDIS_PASSWORD               | Redis password (optional)                                                                                                                                                          | No       |                                                                                  |
| RETRIES                      | The number of retry requests to the provider in case of a failed response                                                                                                          | No       | 2                                                                                |
| SHOW_ABOUT                   | Just set it to `false`, if for some reason you want to hide the `/about` command                                                                                                   | No       | true                                                                             |
| TIMEOUT                      | Timeout (in seconds) for processing requests                                                                                                                                       | No       | 60                                                                               |
| USERS_WHITELIST              | Comma-separated list of whitelisted usernames, i.e. `"@YourName,@YourFriendName,@YourCatName"`                                                                                     | No       |                                                                                  |
| MONITORING_URL               | Activates monitoring functionality and sends GET request to this url every MONITORING_FREQUENCY_CALL seconds.                                                                      | No       |                                                                                  |
| MONITORING_FREQUENCY_CALL    | If monitoring functionality is active sends GET request to MONITORING_URL every MONITORING_FREQUENCY_CALL seconds.                                                                 | No       | 300                                                                              |
| MONITORING_RETRY_CALLS       | Logs error response only after MONITORING_RETRY_CALLS tries.                                                                                                                       | No       | 3                                                                                |
| MONITORING_PROXY             | Monitoring proxy url.                                                                                                                                                              | No       |                                                                                  |

Please, visit the [examples](examples) directory for the example of `.env`-file.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/s-nagaev/hiroshi/tags).

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
