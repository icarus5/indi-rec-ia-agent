from langchain_core.messages import AIMessage, ToolMessage

MAX_LENGTH = 25


def trim_messages(messages):
    num_messages = len(messages)
    if num_messages > MAX_LENGTH:
        messages = messages[-MAX_LENGTH:]
    return messages


def get_tools_result(messages, last_human_index):
    results = []
    for msg in messages[last_human_index:]:
        if isinstance(msg, ToolMessage):
            results.append(msg.content)
    return results


def get_tools_log(messages, last_human_index):
    tools_invocations = []
    for msg in messages[last_human_index:]:
        if isinstance(msg, AIMessage):
            if "tool_calls" in msg.additional_kwargs:
                for tool in msg.additional_kwargs["tool_calls"]:
                    tools_invocations.append(
                        {
                            "tool_name": tool["function"]["name"],
                            "tool_args": tool["function"]["arguments"],
                        }
                    )
    return tools_invocations

def filtered_bad_words_from_ai(messages):
    """
    Filtra los mensajes de tipo AIMessage que tengan indicios de contenido filtrado (malas palabras, groserías, etc.)
    según los campos de content_filter_results o prompt_filter_results.
    Retorna una lista de mensajes AI que fueron detectados con contenido filtrado.
    """
    filtered_messages = []
    for msg in messages:
        if isinstance(msg, AIMessage):
            meta = getattr(msg, 'response_metadata', None) or msg.additional_kwargs.get('response_metadata', {})
            filter_results = meta.get('content_filter_results')
            if not filter_results:
                prompt_filter_results = meta.get('prompt_filter_results')
                if isinstance(prompt_filter_results, list) and prompt_filter_results:
                    filter_results = prompt_filter_results[0].get('content_filter_results')
            if filter_results:
                for key, value in filter_results.items():
                    if isinstance(value, dict) and value.get('filtered') is True:
                        filtered_messages.append(msg)
                        break
    return filtered_messages

