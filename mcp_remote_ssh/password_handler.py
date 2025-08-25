"""Password handling module for SSH sessions following SOLID principles."""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PasswordPrompt:
    """Represents a password prompt detected in SSH output."""
    prompt_type: str  # 'sudo', 'ssh', 'login', etc.
    prompt_text: str  # The actual prompt text
    position: int     # Position in the output where prompt was found
    requires_input: bool = True

@dataclass
class PasswordResponse:
    """Response to a password prompt."""
    password: Optional[str] = None
    timeout: bool = False
    cancelled: bool = False
    error: Optional[str] = None

class PasswordHandler(ABC):
    """Abstract base class for password handlers following Interface Segregation Principle."""
    
    @abstractmethod
    async def detect_prompt(self, output: str) -> Optional[PasswordPrompt]:
        """Detect if output contains a password prompt."""
        pass
    
    @abstractmethod
    async def handle_prompt(self, prompt: PasswordPrompt, context: Dict[str, Any]) -> PasswordResponse:
        """Handle a detected password prompt."""
        pass
    
    @abstractmethod
    def can_handle(self, prompt_type: str) -> bool:
        """Check if this handler can handle a specific prompt type."""
        pass

class SudoPasswordHandler(PasswordHandler):
    """Handles sudo password prompts specifically."""
    
    def __init__(self, sudo_password: Optional[str] = None):
        self.sudo_password = sudo_password
        self.sudo_patterns = [
            r'\[sudo\] password for [^:]+:',
            r'Password:',
            r'sudo: a terminal is required to read the password',
        ]
    
    def can_handle(self, prompt_type: str) -> bool:
        """Check if this handler can handle sudo prompts."""
        return prompt_type == 'sudo'
    
    async def detect_prompt(self, output: str) -> Optional[PasswordPrompt]:
        """Detect sudo password prompts in output."""
        for pattern in self.sudo_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return PasswordPrompt(
                    prompt_type='sudo',
                    prompt_text=match.group(0),
                    position=match.start(),
                    requires_input=True
                )
        return None
    
    async def handle_prompt(self, prompt: PasswordPrompt, context: Dict[str, Any]) -> PasswordResponse:
        """Handle sudo password prompt."""
        if not self.can_handle(prompt.prompt_type):
            return PasswordResponse(error=f"Cannot handle prompt type: {prompt.prompt_type}")
        
        if not self.sudo_password:
            logger.warning("Sudo password not provided, cannot handle prompt")
            return PasswordResponse(error="Sudo password not provided")
        
        logger.info("Handling sudo password prompt")
        return PasswordResponse(password=self.sudo_password)

class InteractivePasswordHandler(PasswordHandler):
    """Handles interactive password prompts by requesting user input."""
    
    def __init__(self, password_callback=None):
        self.password_callback = password_callback
    
    def can_handle(self, prompt_type: str) -> bool:
        """Check if this handler can handle interactive prompts."""
        return prompt_type in ['interactive', 'ssh', 'login', 'sudo']
    
    async def detect_prompt(self, output: str) -> Optional[PasswordPrompt]:
        """Detect interactive password prompts."""
        # Common password prompt patterns
        patterns = [
            r'Password:',
            r'password:',
            r'Enter password:',
            r'\[sudo\] password for [^:]+:',
            r'sudo: a terminal is required to read the password',
            r'SSH password:',
            r'SSH key passphrase:',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return PasswordPrompt(
                    prompt_type='interactive',
                    prompt_text=match.group(0),
                    position=match.start(),
                    requires_input=True
                )
        return None
    
    async def handle_prompt(self, prompt: PasswordPrompt, context: Dict[str, Any]) -> PasswordResponse:
        """Handle interactive password prompt by requesting user input."""
        if self.password_callback:
            try:
                password = await self.password_callback(prompt, context)
                if password:
                    return PasswordResponse(password=password)
                else:
                    return PasswordResponse(cancelled=True)
            except Exception as e:
                return PasswordResponse(error=f"Password callback error: {e}")
        else:
            return PasswordResponse(error="No password callback provided for interactive prompts")

class PasswordManager:
    """Manages multiple password handlers following Single Responsibility Principle."""
    
    def __init__(self):
        self.handlers: List[PasswordHandler] = []
    
    def add_handler(self, handler: PasswordHandler) -> None:
        """Add a password handler."""
        self.handlers.append(handler)
        logger.debug(f"Added password handler: {handler.__class__.__name__}")
    
    def remove_handler(self, handler: PasswordHandler) -> None:
        """Remove a password handler."""
        if handler in self.handlers:
            self.handlers.remove(handler)
            logger.debug(f"Removed password handler: {handler.__class__.__name__}")
    
    async def detect_and_handle_prompt(self, output: str, context: Dict[str, Any]) -> Optional[PasswordResponse]:
        """Detect and handle any password prompt in the output."""
        for handler in self.handlers:
            prompt = await handler.detect_prompt(output)
            if prompt:
                logger.info(f"Detected {prompt.prompt_type} prompt, using {handler.__class__.__name__}")
                return await handler.handle_prompt(prompt, context)
        return None
    
    def get_handler_for_type(self, prompt_type: str) -> Optional[PasswordHandler]:
        """Get the appropriate handler for a prompt type."""
        for handler in self.handlers:
            if handler.can_handle(prompt_type):
                return handler
        return None

# Factory function for creating password managers
def create_password_manager(
    sudo_password: Optional[str] = None,
    interactive_callback=None,
    enable_interactive: bool = True
) -> PasswordManager:
    """Create a password manager with appropriate handlers."""
    manager = PasswordManager()
    
    # Add sudo handler if password is provided
    if sudo_password:
        manager.add_handler(SudoPasswordHandler(sudo_password))
    
    # Add interactive handler if enabled
    if enable_interactive and interactive_callback:
        manager.add_handler(InteractivePasswordHandler(interactive_callback))
    
    return manager
