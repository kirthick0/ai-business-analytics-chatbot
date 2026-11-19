from modules.openai_assistant import (
    configured_api_key,
    configured_model,
    generate_assistant_response,
)


if __name__ == "__main__":
    print(
        generate_assistant_response(
            "What is customer churn rate?",
            api_key=configured_api_key(),
            model=configured_model(),
        )
    )