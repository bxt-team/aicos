# Credits Integration Guide

This guide explains how to integrate credit consumption tracking into existing agents.

## Overview

The credit system tracks usage of AI agents and charges credits based on the actions performed. Each agent action has a configured cost in the `agent_action_costs` table.

## Integration Steps

### 1. For Agents Extending BaseCrew

If your agent extends `BaseCrew`, you can use the built-in credit consumption methods:

```python
class YourAgent(BaseCrew):
    async def generate_content(self, topic: str) -> str:
        # Check if credits are available (optional)
        if not await self.check_credits_available('generate_content'):
            raise InsufficientCreditsError("Not enough credits")
        
        # Consume credits before performing the action
        await self.consume_credits_for_action(
            action='generate_content',
            metadata={'topic': topic}
        )
        
        # Perform the actual work
        result = await self._do_generation(topic)
        
        return result
```

### 2. Using the Decorator Approach

For simpler integration, use the `@consume_credits` decorator:

```python
from app.core.decorators import consume_credits

class ContentAgent(BaseCrew):
    @consume_credits(agent_type='ContentAgent', action='generate_content')
    async def generate_content(self, topic: str, context: dict = None) -> str:
        # The decorator automatically handles credit consumption
        # Just implement your logic
        return await self._do_generation(topic)
```

### 3. Class-Level Decoration

To automatically track all methods in an agent:

```python
from app.core.decorators import track_agent_usage

@track_agent_usage('ContentAgent')
class ContentAgent(BaseCrew):
    async def generate_content(self, topic: str) -> str:
        # Automatically tracked
        return await self._do_generation(topic)
    
    async def create_visual_post(self, prompt: str) -> dict:
        # Also automatically tracked
        return await self._create_visual(prompt)
```

### 4. Manual Credit Consumption

For fine-grained control:

```python
from app.services.credit_service import CreditService

async def process_request(organization_id: str, project_id: str):
    credit_service = CreditService()
    
    # Check balance
    balance = await credit_service.get_balance(organization_id)
    if balance['available'] < 5.0:
        raise InsufficientCreditsError("Insufficient credits")
    
    # Consume credits
    success = await credit_service.consume_credits(
        organization_id=organization_id,
        amount=5.0,
        project_id=project_id,
        agent_type='VideoAgent',
        action='generate_video',
        metadata={'duration': 30}
    )
    
    if not success:
        raise InsufficientCreditsError("Failed to consume credits")
    
    # Perform the work
    result = await generate_video()
    return result
```

## Credit Costs Configuration

Default credit costs are defined in the migration:

| Agent Type | Action | Cost |
|------------|--------|------|
| ContentAgent | generate_content | 1.0 |
| ContentAgent | generate_instagram_reel | 5.0 |
| VisualPostAgent | create_visual_post | 2.0 |
| VoiceAgent | generate_voice | 2.0 |
| VideoAgent | generate_video | 10.0 |
| ResearchAgent | research_topic | 1.0 |
| QAAgent | answer_question | 0.5 |
| WorkflowAgent | execute_workflow | 3.0 |

Update these in the `agent_action_costs` table as needed.

## Context Requirements

Credit consumption requires a valid `RequestContext` with:
- `organization_id` (required)
- `project_id` (optional)
- `department_id` (optional)
- `user_id` (optional)

The context is automatically set by the middleware for API requests.

## Error Handling

Always handle credit-related exceptions:

```python
from app.core.exceptions import InsufficientCreditsError, CreditLimitExceededError

try:
    await agent.consume_credits_for_action('generate_content')
    result = await agent.generate_content()
except InsufficientCreditsError:
    # Handle insufficient credits
    return {"error": "Not enough credits. Please purchase more."}
except CreditLimitExceededError as e:
    # Handle limit exceeded (department limits)
    return {"error": str(e)}
```

## Best Practices

1. **Check Before Consuming**: For expensive operations, check credit availability first
2. **Consume Early**: Consume credits before performing the actual work
3. **Track Metadata**: Include relevant metadata for usage analytics
4. **Handle Errors**: Always handle credit-related exceptions gracefully
5. **Test Without Credits**: Use context-less operations during development

## API Endpoints

- `GET /api/credits/balance` - Get current balance
- `POST /api/credits/use` - Manually consume credits
- `GET /api/credits/usage` - View usage history
- `GET /api/credits/costs` - Get action costs
- `GET /api/billing/plans` - View subscription plans
- `POST /api/billing/purchase-credits` - Buy credit packages

## Testing

To test credit consumption:

```python
# In your tests
async def test_credit_consumption():
    # Set up context
    context = RequestContext(
        organization_id=UUID("..."),
        project_id=UUID("..."),
        user_id=UUID("...")
    )
    
    agent = YourAgent()
    agent.set_context(context)
    
    # Test consumption
    await agent.consume_credits_for_action('test_action')
```