
# def generate_descriptions(action_type, **result_data):
#
#     if action_type.lower() == 'detect':
#         pass
#     elif action_type.lower() == 'categorize':
#         pass
#     elif action_type.lower() == 'classify':
#         pass
#
def generate_descriptions(response_str):
    import json

    try:
        # Parse the string response into a dictionary
        response = json.loads(response_str)

        predicted_class = response.get("predicted_class", "Unknown")
        confidence = response.get("confidence", 0.0)
        class_probabilities = response.get("class_probabilities", {})

        # Construct a descriptive message
        description = f"The model predicts the lesion is {predicted_class} with {confidence * 100:.2f}% confidence."

        # Include probabilities for all classes
        probability_details = "Class probabilities:\n" + "\n".join(
            [f"- {cls}: {prob * 100:.2f}%" for cls, prob in class_probabilities.items()]
        )

        return f"{description}\n\n{probability_details}"

    except json.JSONDecodeError:
        return "Error: Unable to parse response from worker."
