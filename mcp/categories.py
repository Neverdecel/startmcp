"""Provider category definitions."""

from enum import Enum


class ProviderCategory(str, Enum):
    """Categories for organizing MCP providers."""

    ENTERPRISE = "enterprise"
    DEV_TOOLS = "dev_tools"
    DATA = "data"
    CLOUD = "cloud"
    WEB = "web"
    CUSTOM = "custom"


CATEGORY_INFO = {
    ProviderCategory.ENTERPRISE: {
        "display_name": "Enterprise & Collaboration",
        "icon": "🏢",
        "description": "Connect to company SaaS tools (Jira, GitHub, Slack)",
    },
    ProviderCategory.DEV_TOOLS: {
        "display_name": "Development Tools",
        "icon": "🛠️",
        "description": "AI coding assistants and code analysis",
    },
    ProviderCategory.DATA: {
        "display_name": "Data Sources",
        "icon": "💾",
        "description": "Database and data store access",
    },
    ProviderCategory.CLOUD: {
        "display_name": "Cloud Platforms",
        "icon": "☁️",
        "description": "Cloud resource management (AWS, Azure, GCP)",
    },
    ProviderCategory.WEB: {
        "display_name": "Web Services",
        "icon": "🌐",
        "description": "Web scraping and search APIs",
    },
    ProviderCategory.CUSTOM: {
        "display_name": "Custom Providers",
        "icon": "🔧",
        "description": "User-defined custom integrations",
    },
}


def get_category_display_name(category: ProviderCategory) -> str:
    """Get human-readable category name."""
    return CATEGORY_INFO[category]["display_name"]


def get_category_icon(category: ProviderCategory) -> str:
    """Get category icon."""
    return CATEGORY_INFO[category]["icon"]


def get_category_description(category: ProviderCategory) -> str:
    """Get category description."""
    return CATEGORY_INFO[category]["description"]
