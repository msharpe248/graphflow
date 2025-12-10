"""
Comprehensive tests for TemplateResolver and MemoryMixin.

Tests the centralized template resolution system that handles:
- {memory.field} bindings
- {config.field} bindings
- {env.field} bindings
- {secrets.field} bindings
- {{variable}} legacy bindings
"""

import pytest
import os
from graphflow_core import MemoryStore, MemorySchema, FieldDefinition, SecretDefinition, ConfigDefinition, EnvironmentDefinition
from graphflow_core.memory import TemplateResolver
from graphflow_core.steps import MemoryMixin
from graphflow_core.memory.store import _RUNTIME_CONFIG


class TestTemplateResolverBasics:
    """Test basic template resolution functionality."""

    @pytest.fixture
    def simple_schema(self):
        """Create a simple memory schema."""
        return MemorySchema(
            inputs={
                "user_name": FieldDefinition(type="string", required=True),
                "user_id": FieldDefinition(type="number", required=True)
            },
            outputs={
                "greeting": FieldDefinition(type="string", required=True)
            },
            intermediate={
                "processed_name": FieldDefinition(type="string", required=False)
            }
        )

    @pytest.fixture
    def memory(self, simple_schema):
        """Create a memory store with test values."""
        memory = MemoryStore(schema=simple_schema)
        memory.initialize_inputs({"user_name": "Alice", "user_id": 123})
        memory.write("memory.processed_name", "ALICE")
        return memory

    def test_resolve_simple_binding(self, memory):
        """Test resolving a simple memory binding."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("Hello, {memory.user_name}!")
        assert result == "Hello, Alice!"

    def test_resolve_multiple_bindings(self, memory):
        """Test resolving multiple bindings in one string."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("{memory.user_name}'s ID is {memory.user_id}")
        assert result == "Alice's ID is 123"

    def test_resolve_binding_with_number(self, memory):
        """Test resolving a numeric value."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("User ID: {memory.user_id}")
        assert result == "User ID: 123"

    def test_resolve_empty_string(self, memory):
        """Test resolving an empty string."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("")
        assert result == ""

    def test_resolve_no_bindings(self, memory):
        """Test resolving a string with no bindings."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("No bindings here")
        assert result == "No bindings here"

    def test_resolve_missing_key(self, memory):
        """Test resolving a binding with a missing key returns empty string."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("Hello, {memory.nonexistent}!")
        assert result == "Hello, !"

    def test_resolve_intermediate_field(self, memory):
        """Test resolving from intermediate namespace."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("Processed: {memory.processed_name}")
        assert result == "Processed: ALICE"


class TestTemplateResolverNamespaces:
    """Test template resolution across different namespaces."""

    @pytest.fixture(autouse=True)
    def reset_runtime_config(self):
        """Reset global runtime config before each test."""
        global _RUNTIME_CONFIG
        _RUNTIME_CONFIG.clear()
        _RUNTIME_CONFIG.update({
            'cwd': '/test/directory',
            'runtime_url': 'http://localhost:8000'
        })
        yield
        _RUNTIME_CONFIG.clear()

    @pytest.fixture(autouse=True)
    def setup_env_vars(self):
        """Set up test environment variables."""
        os.environ['TEST_API_KEY'] = 'test-key-123'
        os.environ['TEST_DB_URL'] = 'postgresql://localhost'
        os.environ['TEST_SECRET'] = 'super-secret'
        yield
        os.environ.pop('TEST_API_KEY', None)
        os.environ.pop('TEST_DB_URL', None)
        os.environ.pop('TEST_SECRET', None)

    @pytest.fixture
    def full_schema(self):
        """Schema with all namespace types."""
        return MemorySchema(
            inputs={
                "user_name": FieldDefinition(type="string", required=True)
            },
            outputs={
                "result": FieldDefinition(type="string", required=True)
            },
            intermediate={
                "temp_value": FieldDefinition(type="string", required=False)
            },
            config={
                "cwd": ConfigDefinition(type="string"),
                "runtime_url": ConfigDefinition(type="string")
            },
            environment={
                "api_key": EnvironmentDefinition(type="string", key="TEST_API_KEY", required=True),
                "db_url": EnvironmentDefinition(type="string", key="TEST_DB_URL", required=False)
            },
            secrets={
                "db_password": SecretDefinition(provider="env", key="TEST_SECRET")
            }
        )

    @pytest.fixture
    def memory(self, full_schema):
        """Create a memory store with test values."""
        memory = MemoryStore(schema=full_schema)
        memory.initialize_inputs({"user_name": "Bob"})
        return memory

    def test_resolve_config_binding(self, memory):
        """Test resolving config namespace."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("API URL: {config.runtime_url}")
        assert result == "API URL: http://localhost:8000"

    def test_resolve_env_binding(self, memory):
        """Test resolving environment namespace."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("Key: {env.api_key}")
        assert result == "Key: test-key-123"

    def test_resolve_secrets_binding(self, memory):
        """Test resolving secrets namespace."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("Password: {secrets.db_password}")
        assert result == "Password: super-secret"

    def test_resolve_mixed_namespaces(self, memory):
        """Test resolving multiple namespaces in one string."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve(
            "User {memory.user_name} at {config.runtime_url} with key {env.api_key}"
        )
        assert result == "User Bob at http://localhost:8000 with key test-key-123"


class TestTemplateResolverDict:
    """Test resolving templates in dictionaries."""

    @pytest.fixture
    def simple_schema(self):
        """Create a simple memory schema."""
        return MemorySchema(
            inputs={
                "user_id": FieldDefinition(type="string", required=True),
                "api_version": FieldDefinition(type="string", required=True)
            },
            outputs={},
            intermediate={}
        )

    @pytest.fixture
    def memory(self, simple_schema):
        """Create a memory store with test values."""
        memory = MemoryStore(schema=simple_schema)
        memory.initialize_inputs({"user_id": "12345", "api_version": "v2"})
        return memory

    def test_resolve_dict_simple(self, memory):
        """Test resolving a simple dictionary."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve_dict({
            "url": "https://api.example.com/users/{memory.user_id}",
            "version": "{memory.api_version}"
        })
        assert result == {
            "url": "https://api.example.com/users/12345",
            "version": "v2"
        }

    def test_resolve_dict_nested(self, memory):
        """Test resolving a nested dictionary."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve_dict({
            "request": {
                "url": "https://api.example.com/{memory.api_version}/users/{memory.user_id}",
                "headers": {
                    "X-User-ID": "{memory.user_id}"
                }
            }
        })
        assert result == {
            "request": {
                "url": "https://api.example.com/v2/users/12345",
                "headers": {
                    "X-User-ID": "12345"
                }
            }
        }

    def test_resolve_dict_with_non_strings(self, memory):
        """Test that non-string values are preserved."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve_dict({
            "user_id": "{memory.user_id}",
            "timeout": 30,
            "enabled": True,
            "tags": ["test", "prod"]
        })
        assert result == {
            "user_id": "12345",
            "timeout": 30,
            "enabled": True,
            "tags": ["test", "prod"]
        }


class TestTemplateResolverList:
    """Test resolving templates in lists."""

    @pytest.fixture
    def simple_schema(self):
        """Create a simple memory schema."""
        return MemorySchema(
            inputs={
                "item1": FieldDefinition(type="string", required=True),
                "item2": FieldDefinition(type="string", required=True)
            },
            outputs={},
            intermediate={}
        )

    @pytest.fixture
    def memory(self, simple_schema):
        """Create a memory store with test values."""
        memory = MemoryStore(schema=simple_schema)
        memory.initialize_inputs({"item1": "first", "item2": "second"})
        return memory

    def test_resolve_list_simple(self, memory):
        """Test resolving a simple list."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve_list([
            "{memory.item1}",
            "{memory.item2}",
            "static"
        ])
        assert result == ["first", "second", "static"]

    def test_resolve_list_nested(self, memory):
        """Test resolving a nested list with dicts."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve_list([
            {"value": "{memory.item1}"},
            ["{memory.item2}"]
        ])
        assert result == [
            {"value": "first"},
            ["second"]
        ]


class TestTemplateResolverExtractReferences:
    """Test extracting memory references from templates."""

    @pytest.fixture
    def simple_schema(self):
        """Create a simple memory schema."""
        return MemorySchema(inputs={}, outputs={}, intermediate={})

    @pytest.fixture
    def memory(self, simple_schema):
        """Create a memory store."""
        return MemoryStore(schema=simple_schema)

    def test_extract_single_reference(self, memory):
        """Test extracting a single reference."""
        resolver = TemplateResolver(memory)
        refs = resolver.extract_references("Hello {memory.user_name}")
        assert refs == {"memory.user_name"}

    def test_extract_multiple_references(self, memory):
        """Test extracting multiple references."""
        resolver = TemplateResolver(memory)
        refs = resolver.extract_references(
            "{memory.user_name} uses {config.runtime_url} with {secrets.api_key}"
        )
        assert refs == {"memory.user_name", "config.runtime_url", "secrets.api_key"}

    def test_extract_no_references(self, memory):
        """Test extracting from string with no references."""
        resolver = TemplateResolver(memory)
        refs = resolver.extract_references("No bindings here")
        assert refs == set()

    def test_extract_references_from_dict(self, memory):
        """Test extracting references from a dictionary."""
        resolver = TemplateResolver(memory)
        refs = resolver.extract_references_from_dict({
            "url": "{config.api_base}/users/{memory.user_id}",
            "headers": {
                "Authorization": "Bearer {secrets.token}"
            }
        })
        assert refs == {"config.api_base", "memory.user_id", "secrets.token"}


class TestTemplateResolverLegacy:
    """Test legacy {{variable}} pattern support."""

    @pytest.fixture
    def simple_schema(self):
        """Create a simple memory schema."""
        return MemorySchema(
            inputs={
                "user_name": FieldDefinition(type="string", required=True)
            },
            outputs={},
            intermediate={
                "processed": FieldDefinition(type="string", required=False)
            }
        )

    @pytest.fixture
    def memory(self, simple_schema):
        """Create a memory store with test values."""
        memory = MemoryStore(schema=simple_schema)
        memory.initialize_inputs({"user_name": "Charlie"})
        memory.write("memory.processed", "CHARLIE")
        return memory

    def test_legacy_pattern_disabled_by_default(self, memory):
        """Test that legacy patterns are not resolved by default."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("Hello {{user_name}}")
        # Legacy pattern should not be resolved
        assert result == "Hello {{user_name}}"

    def test_legacy_pattern_enabled(self, memory):
        """Test that legacy patterns are resolved when enabled."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("Hello {{user_name}}", allow_legacy=True)
        assert result == "Hello Charlie"

    def test_legacy_pattern_searches_memory_namespaces(self, memory):
        """Test that legacy patterns search inputs, intermediate, outputs."""
        resolver = TemplateResolver(memory)

        # Should find in inputs
        result1 = resolver.resolve("{{user_name}}", allow_legacy=True)
        assert result1 == "Charlie"

        # Should find in intermediate
        result2 = resolver.resolve("{{processed}}", allow_legacy=True)
        assert result2 == "CHARLIE"

    def test_has_legacy_bindings(self, memory):
        """Test detecting legacy bindings."""
        resolver = TemplateResolver(memory)

        assert resolver.has_legacy_bindings("Hello {{user_name}}")
        assert not resolver.has_legacy_bindings("Hello {memory.user_name}")
        assert not resolver.has_legacy_bindings("No bindings")


class TestTemplateResolverHasBindings:
    """Test detecting bindings in templates."""

    @pytest.fixture
    def simple_schema(self):
        """Create a simple memory schema."""
        return MemorySchema(inputs={}, outputs={}, intermediate={})

    @pytest.fixture
    def memory(self, simple_schema):
        """Create a memory store."""
        return MemoryStore(schema=simple_schema)

    def test_has_bindings_with_binding(self, memory):
        """Test detecting bindings in a string with bindings."""
        resolver = TemplateResolver(memory)
        assert resolver.has_bindings("Hello {memory.user_name}")

    def test_has_bindings_without_binding(self, memory):
        """Test detecting no bindings."""
        resolver = TemplateResolver(memory)
        assert not resolver.has_bindings("No bindings here")

    def test_has_bindings_empty_string(self, memory):
        """Test detecting bindings in empty string."""
        resolver = TemplateResolver(memory)
        assert not resolver.has_bindings("")

    def test_has_bindings_all_namespaces(self, memory):
        """Test detecting bindings from all namespaces."""
        resolver = TemplateResolver(memory)

        assert resolver.has_bindings("{memory.field}")
        assert resolver.has_bindings("{config.field}")
        assert resolver.has_bindings("{env.field}")
        assert resolver.has_bindings("{secrets.field}")


class TestMemoryStoreResolverIntegration:
    """Test MemoryStore integration with TemplateResolver."""

    @pytest.fixture
    def simple_schema(self):
        """Create a simple memory schema."""
        return MemorySchema(
            inputs={
                "user_name": FieldDefinition(type="string", required=True)
            },
            outputs={},
            intermediate={}
        )

    @pytest.fixture
    def memory(self, simple_schema):
        """Create a memory store with test values."""
        memory = MemoryStore(schema=simple_schema)
        memory.initialize_inputs({"user_name": "Diana"})
        return memory

    def test_get_resolver(self, memory):
        """Test getting a resolver from memory store."""
        resolver = memory.get_resolver()
        assert isinstance(resolver, TemplateResolver)

    def test_resolve_template_convenience_method(self, memory):
        """Test the convenience resolve_template method."""
        result = memory.resolve_template("Hello, {memory.user_name}!")
        assert result == "Hello, Diana!"


class TestMemoryMixin:
    """Test the MemoryMixin class for step implementations."""

    @pytest.fixture
    def simple_schema(self):
        """Create a simple memory schema."""
        return MemorySchema(
            inputs={
                "input_value": FieldDefinition(type="string", required=True)
            },
            outputs={
                "output_value": FieldDefinition(type="string", required=True)
            },
            intermediate={
                "temp_value": FieldDefinition(type="string", required=False)
            }
        )

    @pytest.fixture
    def memory(self, simple_schema):
        """Create a memory store with test values."""
        memory = MemoryStore(schema=simple_schema)
        memory.initialize_inputs({"input_value": "test_input"})
        return memory

    def test_mixin_resolve(self, memory):
        """Test MemoryMixin._resolve method."""
        mixin = MemoryMixin()
        result = mixin._resolve("Value: {memory.input_value}", memory)
        assert result == "Value: test_input"

    def test_mixin_resolve_dict(self, memory):
        """Test MemoryMixin._resolve_dict method."""
        mixin = MemoryMixin()
        result = mixin._resolve_dict({
            "key": "{memory.input_value}"
        }, memory)
        assert result == {"key": "test_input"}

    def test_mixin_get_value_with_namespace(self, memory):
        """Test MemoryMixin._get_value with namespace prefix."""
        mixin = MemoryMixin()
        result = mixin._get_value("memory.input_value", memory)
        assert result == "test_input"

    def test_mixin_get_value_without_namespace(self, memory):
        """Test MemoryMixin._get_value without namespace prefix."""
        mixin = MemoryMixin()
        result = mixin._get_value("input_value", memory)
        assert result == "test_input"

    def test_mixin_get_value_default(self, memory):
        """Test MemoryMixin._get_value with default.

        Note: MemoryStore returns empty string for missing memory keys (graceful handling),
        so the default is only used for non-memory namespaces that raise KeyError.
        """
        mixin = MemoryMixin()
        # Memory namespace returns "" for missing keys (graceful handling)
        result = mixin._get_value("nonexistent", memory)
        assert result == ""

        # Test with a key that would raise KeyError (config namespace)
        result2 = mixin._get_value("config.nonexistent", memory, default="default_value")
        assert result2 == "default_value"

    def test_mixin_write_output_with_namespace(self, memory):
        """Test MemoryMixin._write_output with namespace prefix."""
        mixin = MemoryMixin()
        mixin._write_output("memory.temp_value", "written_value", memory)
        assert memory.read("memory.temp_value") == "written_value"

    def test_mixin_write_output_without_namespace(self, memory):
        """Test MemoryMixin._write_output without namespace prefix."""
        mixin = MemoryMixin()
        mixin._write_output("temp_value", "written_value", memory)
        assert memory.read("memory.temp_value") == "written_value"

    def test_mixin_has_bindings(self, memory):
        """Test MemoryMixin._has_bindings method."""
        mixin = MemoryMixin()
        assert mixin._has_bindings("{memory.input_value}", memory)
        assert not mixin._has_bindings("no bindings", memory)

    def test_mixin_extract_references(self, memory):
        """Test MemoryMixin._extract_references method."""
        mixin = MemoryMixin()
        refs = mixin._extract_references("{memory.input_value} and {config.setting}", memory)
        assert refs == {"memory.input_value", "config.setting"}


class TestTemplateResolverEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.fixture
    def simple_schema(self):
        """Create a simple memory schema."""
        return MemorySchema(
            inputs={
                "empty_value": FieldDefinition(type="string", required=False, default=""),
                "none_value": FieldDefinition(type="any", required=False)
            },
            outputs={},
            intermediate={}
        )

    @pytest.fixture
    def memory(self, simple_schema):
        """Create a memory store."""
        memory = MemoryStore(schema=simple_schema)
        memory.initialize_inputs({"empty_value": "", "none_value": None})
        return memory

    def test_resolve_empty_value(self, memory):
        """Test resolving a binding to an empty string."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("Value: {memory.empty_value}!")
        assert result == "Value: !"

    def test_resolve_none_value(self, memory):
        """Test resolving a binding to None."""
        resolver = TemplateResolver(memory)
        result = resolver.resolve("Value: {memory.none_value}!")
        assert result == "Value: !"

    def test_resolve_nested_field_names(self):
        """Test resolving field names with dots (nested paths)."""
        schema = MemorySchema(
            inputs={},
            outputs={},
            intermediate={
                "step.output.value": FieldDefinition(type="string", required=False, default="nested")
            }
        )
        memory = MemoryStore(schema=schema)
        resolver = TemplateResolver(memory)

        result = resolver.resolve("Result: {memory.step.output.value}")
        assert result == "Result: nested"

    def test_resolve_special_characters_in_value(self):
        """Test resolving values with special characters."""
        schema = MemorySchema(
            inputs={
                "special": FieldDefinition(type="string", required=True)
            },
            outputs={},
            intermediate={}
        )
        memory = MemoryStore(schema=schema)
        memory.initialize_inputs({"special": "value with {braces} and $special chars"})
        resolver = TemplateResolver(memory)

        result = resolver.resolve("Got: {memory.special}")
        assert result == "Got: value with {braces} and $special chars"

    def test_resolve_unicode_values(self):
        """Test resolving values with unicode characters."""
        schema = MemorySchema(
            inputs={
                "unicode": FieldDefinition(type="string", required=True)
            },
            outputs={},
            intermediate={}
        )
        memory = MemoryStore(schema=schema)
        memory.initialize_inputs({"unicode": "Hello, \u4e16\u754c! \ud83c\udf0d"})
        resolver = TemplateResolver(memory)

        result = resolver.resolve("Message: {memory.unicode}")
        assert result == "Message: Hello, \u4e16\u754c! \ud83c\udf0d"
