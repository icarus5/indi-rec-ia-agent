import logging
from functools import lru_cache
from langgraph.prebuilt import create_react_agent
import traceback

from src.ai.llm import get_model
from src.ai.tools.registry import get_tools_acreetor
from src.utils.date.date_utils import get_current_day, get_current_day_name
from src.ai.prompts.base import get_prompt
from src.ai.memory import RedisMemory

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, user_id, shared_state, session_id='', invoke_id=''):
        self.user_id = user_id
        self.shared_state = shared_state
        self.model = get_model()
        self.username = shared_state.get("username")
        self.system_prompt = ""
        self.tools = []
        self.executor = None
        self.session_id = session_id
        self.invoke_id = invoke_id


    def set_system_prompt(self, prompt):
        self.system_prompt = prompt

    def set_tools(self, tools):
        self.tools = tools

    def build_agent_executor(self):
        if self.model is None:
            logger.error(f"Session ID: {self.session_id} - Invoke ID: {self.invoke_id} - Model is None")
            return None
        try:
            self.executor = create_react_agent(
                self.model, 
                self.tools, 
                prompt=self.system_prompt, 
                debug=False
            )
        except Exception as e:
            logging.info(f"Error: {e}")
            traceback.print_exc()
            return None


@lru_cache(maxsize=None)
def cached_get_prompt(prompt_key, session_id='', invoke_id=''):
    return get_prompt(prompt_key, session_id, invoke_id)


def build_agent(type_agent, user_id, shared_state, memory: RedisMemory, session_id='', invoke_id='', is_chit_chat=False):
    logging.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Build agent")
    name_agent = "Indibot"
    today = get_current_day()
    day_name = get_current_day_name()
    username = shared_state.get("username")

    if type_agent == "acreetor":
        agent = Agent(user_id=user_id, shared_state=shared_state, session_id=session_id, invoke_id=invoke_id)
        agent.set_tools(get_tools_acreetor(user_id, shared_state, memory, session_id, invoke_id))
        pre_prompt = cached_get_prompt("AZURE_INDEPENDENT_PROMPT_ID", session_id=session_id, invoke_id=invoke_id)
        prompt = pre_prompt.format(
            name_agent=name_agent,
            username=username,
            day_name=day_name, 
            today=today,
        )
        agent.set_system_prompt(prompt)
        agent.build_agent_executor()
        return agent
    elif type_agent == "enterprise":
        agent = Agent(user_id=user_id, shared_state=shared_state, session_id=session_id, invoke_id=invoke_id)
        if is_chit_chat:
            agent.set_tools(get_tools_acreetor(user_id, shared_state, memory, session_id, invoke_id))
            pre_prompt = cached_get_prompt("AZURE_ENTERPRISE_PROMPT_ID", session_id=session_id, invoke_id=invoke_id)
            prompt = pre_prompt.format(
                name_agent=name_agent,
                username=username,
                day_name=day_name, 
                today=today,
            )
            agent.set_system_prompt(prompt)
            agent.build_agent_executor()
        else:
             agent.executor = False
        return agent
    else:
        agent = Agent(user_id=user_id, shared_state=shared_state)
        pre_prompt = cached_get_prompt("AZURE_ANONYMOUS_PROMPT_ID")
        prompt = pre_prompt.format(
            name_agent=name_agent,
            username=username,
            day_name=day_name, 
            today=today
        )
        agent.set_system_prompt(prompt)
        agent.build_agent_executor()
        return agent
