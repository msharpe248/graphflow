"""
Comprehensive tests for MemoryStore implementation.

Tests all 6 namespaces: inputs, outputs, intermediate, config, environment, secrets
Tests both namespaced and legacy syntax patterns
Tests all usage patterns used throughout GraphFlow project
"""

import pytest
import os
from graphflow_core import MemoryStore, MemorySchema, FieldDefinition, SecretDefinition, ConfigDefinition, EnvironmentDefinition
from graphflow_core.memory.store import _RUNTIME_CONFIG


class TestMemoryStoreBasics:
    """Test basic memory store initialization and operations."""

    @pytest.fixture
    def simple_schema(self):
        """Create a simple memory schema."""
        return MemorySchema(
            inputs={
                "user_input": FieldDefinition(type="string", required=True)
            },
            outputs={
                "final_result": FieldDefinition(type="string", required=True)
            },
            intermediate={
                "temp_value": FieldDefinition(type="string", required=False)
            }
        )

    def test_memory_initialization(self, simple_schema):
        """Test creating a memory store with schema."""
        memory = MemoryStore(schema=simple_schema)

        assert memory.schema == simple_schema
        assert not memory._initialized

    def test_initialize_inputs_with_required_field(self, simple_schema):
        """Test initializing inputs with required field."""
        memory = MemoryStore(schema=simple_schema)
        memory.initialize_inputs({"user_input": "hello world"})

        assert memory._initialized
        assert memory.read("user_input") == "hello world"

    def test_initialize_inputs_missing_required_field(self, simple_schema):
        """Test that missing required input raises error."""
        memory = MemoryStore(schema=simple_schema)

        with pytest.raises(ValueError, match="Required input missing"):
            memory.initialize_inputs({})

    def test_initialize_inputs_with_defaults(self):
        """Test that default values are applied for missing inputs."""
        schema = MemorySchema(
            inputs={
                "url": FieldDefinition(type="string", required=False, default="https://example.com"),
                "timeout": FieldDefinition(type="number", required=False, default=30)
            },
            outputs={},
            intermediate={}
        )

        memory = MemoryStore(schema=schema)
        memory.initialize_inputs({})

        assert memory.read("url") == "https://example.com"
        assert memory.read("timeout") == 30

    def test_initialize_intermediate_and_output_defaults(self):
        """Test that intermediate and output fields get default values on init."""
        schema = MemorySchema(
            inputs={},
            outputs={
                "result": FieldDefinition(type="string", required=False, default="")
            },
            intermediate={
                "counter": FieldDefinition(type="number", required=False, default=0),
                "enabled": FieldDefinition(type="boolean", required=False, default=True)
            }
        )

        memory = MemoryStore(schema=schema)

        # Should have default values set on initialization
        assert memory.read("counter") == 0
        assert memory.read("enabled") is True
        assert memory.read("result") == ""


class TestMemoryNamespaces:
    """Test namespaced memory access patterns."""

    @pytest.fixture
    def namespaced_schema(self):
        """Create schema with all namespace types."""
        return MemorySchema(
            inputs={
                "user_name": FieldDefinition(type="string", required=True)
            },
            outputs={
                "greeting": FieldDefinition(type="string", required=True)
            },
            intermediate={
                "processed_name": FieldDefinition(type="string", required=False)
            },
            config={
                "cwd": ConfigDefinition(type="string", description="Current working directory"),
                "runtime_url": ConfigDefinition(type="string", description="Runtime API URL")
            },
            environment={
                "api_key": EnvironmentDefinition(type="string", key="TEST_API_KEY", required=False)
            },
            secrets={
                "db_password": SecretDefinition(provider="env", key="DB_PASSWORD")
            }
        )

    def test_namespaced_read_memory(self, namespaced_schema):
        """Test reading from memory namespace using {memory.field} syntax."""
        memory = MemoryStore(schema=namespaced_schema)
        memory.initialize_inputs({"user_name": "Alice"})

        # Namespaced read
        assert memory.read("memory.user_name") == "Alice"

        # Write to intermediate
        memory.write("memory.processed_name", "ALICE")
        assert memory.read("memory.processed_name") == "ALICE"

        # Write to output
        memory.write("memory.greeting", "Hello, ALICE!")
        assert memory.read("memory.greeting") == "Hello, ALICE!"

    def test_legacy_read_memory(self, namespaced_schema):
        """Test reading without namespace prefix (legacy compatibility)."""
        memory = MemoryStore(schema=namespaced_schema)
        memory.initialize_inputs({"user_name": "Bob"})

        # Legacy read (no namespace)
        assert memory.read("user_name") == "Bob"

        # Legacy write
        memory.write("processed_name", "BOB")
        assert memory.read("processed_name") == "BOB"

    def test_read_from_unknown_memory_key(self, namespaced_schema):
        """Test reading from non-existent memory key raises error."""
        memory = MemoryStore(schema=namespaced_schema)
        memory.initialize_inputs({"user_name": "Charlie"})

        with pytest.raises(KeyError, match="Memory key not found"):
            memory.read("memory.nonexistent_field")

    def test_write_to_unknown_memory_key(self, namespaced_schema):
        """Test writing to non-existent memory key raises error."""
        memory = MemoryStore(schema=namespaced_schema)
        memory.initialize_inputs({"user_name": "Diana"})

        with pytest.raises(KeyError, match="Memory key not in schema"):
            memory.write("memory.unknown_field", "value")


class TestConfigNamespace:
    """Test config namespace behavior (global, read-only)."""

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

    @pytest.fixture
    def config_schema(self):
        """Schema with config namespace."""
        return MemorySchema(
            inputs={},
            outputs={},
            intermediate={},
            config={
                "cwd": ConfigDefinition(type="string"),
                "runtime_url": ConfigDefinition(type="string")
            }
        )

    def test_read_from_config_namespace(self, config_schema):
        """Test reading from config namespace proxies to global runtime config."""
        memory = MemoryStore(schema=config_schema)

        # Should read from global _RUNTIME_CONFIG
        assert memory.read("config.cwd") == "/test/directory"
        assert memory.read("config.runtime_url") == "http://localhost:8000"

    def test_populate_config(self, config_schema):
        """Test populating config values updates global registry."""
        memory = MemoryStore(schema=config_schema)

        # Populate config
        memory.populate_config({
            'cwd': '/new/directory',
            'runtime_url': 'http://localhost:9000'
        })

        # Should read updated values
        assert memory.read("config.cwd") == "/new/directory"
        assert memory.read("config.runtime_url") == "http://localhost:9000"

        # Global registry should be updated
        assert _RUNTIME_CONFIG['cwd'] == "/new/directory"

    def test_config_namespace_is_read_only(self, config_schema):
        """Test that writing to config namespace raises error."""
        memory = MemoryStore(schema=config_schema)

        with pytest.raises(ValueError, match="Config namespace is read-only"):
            memory.write("config.cwd", "/new/value")

    def test_get_all_config(self, config_schema):
        """Test getting all config values."""
        memory = MemoryStore(schema=config_schema)

        all_config = memory.get_all_config()

        assert all_config['cwd'] == "/test/directory"
        assert all_config['runtime_url'] == "http://localhost:8000"

    def test_config_shared_across_memory_instances(self, config_schema):
        """Test that config is shared globally across MemoryStore instances."""
        memory1 = MemoryStore(schema=config_schema)
        memory2 = MemoryStore(schema=config_schema)

        # Populate config in first instance
        memory1.populate_config({'cwd': '/shared/directory'})

        # Should be visible in second instance
        assert memory2.read("config.cwd") == "/shared/directory"


class TestEnvironmentNamespace:
    """Test environment namespace behavior (proxy to os.environ)."""

    @pytest.fixture(autouse=True)
    def setup_env_vars(self):
        """Set up test environment variables."""
        os.environ['TEST_API_KEY'] = 'test-key-123'
        os.environ['TEST_DB_URL'] = 'postgresql://localhost'
        yield
        # Clean up
        os.environ.pop('TEST_API_KEY', None)
        os.environ.pop('TEST_DB_URL', None)

    @pytest.fixture
    def env_schema(self):
        """Schema with environment namespace."""
        return MemorySchema(
            inputs={},
            outputs={},
            intermediate={},
            environment={
                "api_key": EnvironmentDefinition(type="string", key="TEST_API_KEY", required=True),
                "db_url": EnvironmentDefinition(type="string", key="TEST_DB_URL", required=False)
            }
        )

    def test_read_from_environment_namespace(self, env_schema):
        """Test reading from environment namespace proxies to os.environ."""
        memory = MemoryStore(schema=env_schema)

        # Should read from os.environ
        assert memory.read("env.api_key") == "test-key-123"
        assert memory.read("env.db_url") == "postgresql://localhost"

    def test_write_to_environment_namespace(self, env_schema):
        """Test writing to environment namespace updates os.environ."""
        memory = MemoryStore(schema=env_schema)

        # Write to environment
        memory.write("env.api_key", "new-key-456")

        # Should update os.environ
        assert os.environ['TEST_API_KEY'] == "new-key-456"

        # Should read back new value
        assert memory.read("env.api_key") == "new-key-456"

    def test_get_all_environment(self, env_schema):
        """Test getting all environment variables returns full os.environ."""
        memory = MemoryStore(schema=env_schema)

        all_env = memory.get_all_environment()

        # Should return ALL environment variables, not just schema-defined ones
        assert 'TEST_API_KEY' in all_env
        assert 'PATH' in all_env  # System env var
        assert all_env['TEST_API_KEY'] == 'test-key-123'

    def test_missing_required_env_var(self, env_schema):
        """Test reading missing required environment variable raises error."""
        # Remove the env var
        os.environ.pop('TEST_API_KEY', None)

        memory = MemoryStore(schema=env_schema)

        with pytest.raises(KeyError, match="Environment variable not set"):
            memory.read("env.api_key")

    def test_environment_not_in_schema(self, env_schema):
        """Test reading environment variable not in schema raises error."""
        memory = MemoryStore(schema=env_schema)

        with pytest.raises(KeyError, match="Environment key not in schema"):
            memory.read("env.nonexistent_var")


class TestSecretsNamespace:
    """Test secrets namespace behavior."""

    @pytest.fixture(autouse=True)
    def setup_secrets(self):
        """Set up test secret in environment."""
        os.environ['TEST_DB_PASSWORD'] = 'super-secret-123'
        yield
        os.environ.pop('TEST_DB_PASSWORD', None)

    @pytest.fixture
    def secrets_schema(self):
        """Schema with secrets namespace."""
        return MemorySchema(
            inputs={},
            outputs={},
            intermediate={},
            secrets={
                "db_password": SecretDefinition(
                    provider="env",
                    key="TEST_DB_PASSWORD",
                    description="Database password"
                )
            }
        )

    def test_read_secret_from_env_provider(self, secrets_schema):
        """Test reading secret with env provider."""
        memory = MemoryStore(schema=secrets_schema)

        # Should load from environment variable
        secret_value = memory.read("secrets.db_password")
        assert secret_value == "super-secret-123"

    def test_secret_caching(self, secrets_schema):
        """Test that secrets are cached after first read."""
        memory = MemoryStore(schema=secrets_schema)

        # First read
        secret1 = memory.read("secrets.db_password")

        # Change env var
        os.environ['TEST_DB_PASSWORD'] = 'new-password'

        # Second read should return cached value
        secret2 = memory.read("secrets.db_password")
        assert secret2 == "super-secret-123"  # Cached value

    def test_write_to_secrets_namespace(self, secrets_schema):
        """Test writing to secrets namespace."""
        memory = MemoryStore(schema=secrets_schema)

        # Can write to secrets at runtime
        memory.write("secrets.db_password", "runtime-secret")

        # Should read back written value
        assert memory.read("secrets.db_password") == "runtime-secret"

    def test_secret_not_in_schema(self, secrets_schema):
        """Test reading secret not in schema raises error."""
        memory = MemoryStore(schema=secrets_schema)

        with pytest.raises(KeyError):
            memory.read("secrets.nonexistent_secret")

    def test_missing_secret_env_var(self):
        """Test reading secret with missing env var raises error."""
        schema = MemorySchema(
            secrets={
                "missing_secret": SecretDefinition(provider="env", key="MISSING_VAR")
            }
        )

        memory = MemoryStore(schema=schema)

        with pytest.raises(ValueError, match="Environment variable not set"):
            memory.read("secrets.missing_secret")

    def test_vault_provider_not_implemented(self):
        """Test that vault provider raises NotImplementedError."""
        schema = MemorySchema(
            secrets={
                "vault_secret": SecretDefinition(provider="vault", key="secret/db/password")
            }
        )

        memory = MemoryStore(schema=schema)

        with pytest.raises(NotImplementedError, match="Vault provider not yet implemented"):
            memory.read("secrets.vault_secret")

    def test_aws_secrets_provider_not_implemented(self):
        """Test that aws_secrets provider raises NotImplementedError."""
        schema = MemorySchema(
            secrets={
                "aws_secret": SecretDefinition(provider="aws_secrets", key="prod/db/password")
            }
        )

        memory = MemoryStore(schema=schema)

        with pytest.raises(NotImplementedError, match="AWS Secrets Manager not yet implemented"):
            memory.read("secrets.aws_secret")


class TestMemoryOperations:
    """Test various memory operations."""

    @pytest.fixture
    def full_schema(self):
        """Schema with all field types."""
        return MemorySchema(
            inputs={
                "string_input": FieldDefinition(type="string", required=True),
                "number_input": FieldDefinition(type="number", required=False, default=42),
                "boolean_input": FieldDefinition(type="boolean", required=False, default=True),
                "object_input": FieldDefinition(type="object", required=False, default={}),
                "array_input": FieldDefinition(type="array", required=False, default=[])
            },
            outputs={
                "result": FieldDefinition(type="string", required=True)
            },
            intermediate={
                "temp1": FieldDefinition(type="string", required=False),
                "temp2": FieldDefinition(type="number", required=False)
            }
        )

    def test_get_all_inputs(self, full_schema):
        """Test getting all input values."""
        memory = MemoryStore(schema=full_schema)
        memory.initialize_inputs({"string_input": "test"})

        inputs = memory.get_all_inputs()

        assert inputs['string_input'] == "test"
        assert inputs['number_input'] == 42
        assert inputs['boolean_input'] is True

    def test_get_all_outputs(self, full_schema):
        """Test getting all output values."""
        memory = MemoryStore(schema=full_schema)
        memory.initialize_inputs({"string_input": "test"})
        memory.write("result", "final value")

        outputs = memory.get_all_outputs()

        assert outputs['result'] == "final value"

    def test_get_all_intermediate(self, full_schema):
        """Test getting all intermediate values."""
        memory = MemoryStore(schema=full_schema)
        memory.initialize_inputs({"string_input": "test"})
        memory.write("temp1", "intermediate1")
        memory.write("temp2", 123)

        intermediate = memory.get_all_intermediate()

        assert intermediate['temp1'] == "intermediate1"
        assert intermediate['temp2'] == 123

    def test_to_dict(self, full_schema):
        """Test converting memory to dictionary."""
        memory = MemoryStore(schema=full_schema)
        memory.initialize_inputs({"string_input": "test"})
        memory.write("result", "output")
        memory.write("temp1", "temp")

        mem_dict = memory.to_dict()

        assert 'memory' in mem_dict
        assert 'config' in mem_dict
        assert 'environment' in mem_dict
        assert 'secrets' in mem_dict

        assert mem_dict['memory']['inputs']['string_input'] == "test"
        assert mem_dict['memory']['outputs']['result'] == "output"
        assert mem_dict['memory']['intermediate']['temp1'] == "temp"

    def test_has_key(self, full_schema):
        """Test checking if key exists in memory."""
        memory = MemoryStore(schema=full_schema)
        memory.initialize_inputs({"string_input": "test"})

        assert memory.has_key("string_input")
        assert not memory.has_key("nonexistent")

    def test_clear_intermediate(self, full_schema):
        """Test clearing intermediate values."""
        memory = MemoryStore(schema=full_schema)
        memory.initialize_inputs({"string_input": "test"})
        memory.write("temp1", "value1")
        memory.write("temp2", 42)

        # Clear intermediate
        memory.clear_intermediate()

        intermediate = memory.get_all_intermediate()
        assert len(intermediate) == 0


class TestMemoryZeroValues:
    """Test zero value initialization for different field types."""

    def test_string_zero_value(self):
        """Test string fields initialize to empty string."""
        schema = MemorySchema(
            intermediate={
                "str_field": FieldDefinition(type="string", required=False)
            }
        )

        memory = MemoryStore(schema=schema)
        assert memory.read("str_field") == ""

    def test_number_zero_value(self):
        """Test number fields initialize to 0."""
        schema = MemorySchema(
            intermediate={
                "num_field": FieldDefinition(type="number", required=False)
            }
        )

        memory = MemoryStore(schema=schema)
        assert memory.read("num_field") == 0

    def test_boolean_zero_value(self):
        """Test boolean fields initialize to False."""
        schema = MemorySchema(
            intermediate={
                "bool_field": FieldDefinition(type="boolean", required=False)
            }
        )

        memory = MemoryStore(schema=schema)
        assert memory.read("bool_field") is False

    def test_object_zero_value(self):
        """Test object fields initialize to empty dict."""
        schema = MemorySchema(
            intermediate={
                "obj_field": FieldDefinition(type="object", required=False)
            }
        )

        memory = MemoryStore(schema=schema)
        assert memory.read("obj_field") == {}

    def test_array_zero_value(self):
        """Test array fields initialize to empty list."""
        schema = MemorySchema(
            intermediate={
                "arr_field": FieldDefinition(type="array", required=False)
            }
        )

        memory = MemoryStore(schema=schema)
        assert memory.read("arr_field") == []

    def test_any_zero_value(self):
        """Test any fields initialize to None."""
        schema = MemorySchema(
            intermediate={
                "any_field": FieldDefinition(type="any", required=False)
            }
        )

        memory = MemoryStore(schema=schema)
        assert memory.read("any_field") is None


class TestMemoryValidation:
    """Test memory validation and reference checking."""

    @pytest.fixture(autouse=True)
    def reset_runtime_config(self):
        """Reset global runtime config."""
        global _RUNTIME_CONFIG
        _RUNTIME_CONFIG.clear()
        _RUNTIME_CONFIG.update({'cwd': '/test', 'runtime_url': 'http://localhost:8000'})
        yield
        _RUNTIME_CONFIG.clear()

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Set up environment variables."""
        os.environ['TEST_VAR'] = 'test-value'
        yield
        os.environ.pop('TEST_VAR', None)

    def test_validate_references_all_present(self):
        """Test validation passes when all references are present."""
        schema = MemorySchema(
            config={
                "cwd": ConfigDefinition(type="string")
            },
            environment={
                "test_var": EnvironmentDefinition(type="string", key="TEST_VAR", required=True)
            },
            secrets={
                "db_pass": SecretDefinition(provider="env", key="TEST_VAR")
            }
        )

        memory = MemoryStore(schema=schema)

        warnings = memory.validate_references()

        # Should have no warnings - all values present
        assert len(warnings) == 0

    def test_validate_references_missing_config(self):
        """Test validation warns about missing config values."""
        schema = MemorySchema(
            config={
                "missing_config": ConfigDefinition(type="string")
            }
        )

        memory = MemoryStore(schema=schema)

        warnings = memory.validate_references()

        assert len(warnings) == 1
        assert "missing_config" in warnings[0]

    def test_validate_references_missing_env_var(self):
        """Test validation warns about missing environment variables."""
        schema = MemorySchema(
            environment={
                "missing_var": EnvironmentDefinition(type="string", key="MISSING_ENV", required=True)
            }
        )

        memory = MemoryStore(schema=schema)

        warnings = memory.validate_references()

        assert len(warnings) >= 1
        assert any("MISSING_ENV" in w for w in warnings)


class TestMemoryUsagePatterns:
    """Test common usage patterns in GraphFlow."""

    def test_http_plugin_pattern(self):
        """Test memory pattern used by HTTP plugin."""
        schema = MemorySchema(
            inputs={
                "url": FieldDefinition(type="string", required=False, default="https://example.com")
            },
            outputs={
                "page": FieldDefinition(type="string", required=True)
            },
            intermediate={
                "http.HTTPGetStep_2.timeout": FieldDefinition(type="number", default=30),
                "http.HTTPGetStep_2.retries": FieldDefinition(type="number", default=2),
                "http.HTTPGetStep_2.verify_ssl": FieldDefinition(type="boolean", default=True),
                "http.HTTPGetStep_2.response": FieldDefinition(type="string", required=False)
            }
        )

        memory = MemoryStore(schema=schema)
        memory.initialize_inputs({})  # Uses default URL

        # Read config values (with defaults)
        assert memory.read("memory.http.HTTPGetStep_2.timeout") == 30
        assert memory.read("memory.http.HTTPGetStep_2.retries") == 2
        assert memory.read("memory.http.HTTPGetStep_2.verify_ssl") is True

        # Simulate HTTP step writing response
        memory.write("memory.http.HTTPGetStep_2.response", "<html>...</html>")

        # Write to output
        memory.write("memory.page", "<html>...</html>")

        outputs = memory.get_all_outputs()
        assert outputs['page'] == "<html>...</html>"

    def test_runtime_config_pattern(self):
        """Test runtime config injection pattern used by executor."""
        global _RUNTIME_CONFIG

        schema = MemorySchema(
            inputs={},
            outputs={},
            config={
                "cwd": ConfigDefinition(type="string"),
                "runtime_url": ConfigDefinition(type="string")
            }
        )

        memory = MemoryStore(schema=schema)

        # Runtime executor populates config before execution
        memory.populate_config({
            'cwd': os.getcwd(),
            'runtime_url': 'http://localhost:8000'
        })

        # Graph can read config values
        assert memory.read("config.cwd") == os.getcwd()
        assert memory.read("config.runtime_url") == "http://localhost:8000"

        # Config should be in to_dict output
        mem_dict = memory.to_dict()
        assert mem_dict['config']['cwd'] == os.getcwd()

    def test_write_memory_step_pattern(self):
        """Test pattern used by write-memory builtin step."""
        schema = MemorySchema(
            inputs={},
            outputs={
                "final_value": FieldDefinition(type="string", required=True)
            },
            intermediate={
                "source_value": FieldDefinition(type="string", required=False)
            }
        )

        memory = MemoryStore(schema=schema)

        # Write to intermediate (simulating earlier step)
        memory.write("memory.source_value", "computed result")

        # Write-memory step copies from source to output
        source = memory.read("memory.source_value")
        memory.write("memory.final_value", source)

        outputs = memory.get_all_outputs()
        assert outputs['final_value'] == "computed result"


class TestMemoryErrorCases:
    """Test error handling in memory operations."""

    def test_unknown_namespace(self):
        """Test reading from unknown namespace raises error."""
        schema = MemorySchema(inputs={})
        memory = MemoryStore(schema=schema)

        with pytest.raises(KeyError, match="Unknown namespace"):
            memory.read("unknown.field")

    def test_write_to_input_field_fails(self):
        """Test that writing to input fields is not allowed."""
        schema = MemorySchema(
            inputs={
                "input_field": FieldDefinition(type="string", required=True)
            }
        )

        memory = MemoryStore(schema=schema)
        memory.initialize_inputs({"input_field": "original"})

        # Cannot write to inputs using legacy syntax
        with pytest.raises(KeyError, match="Memory key not in schema"):
            memory.write("input_field", "modified")

    def test_invalid_input_key(self):
        """Test that invalid input key raises error."""
        schema = MemorySchema(
            inputs={
                "valid_input": FieldDefinition(type="string", required=True)
            }
        )

        memory = MemoryStore(schema=schema)

        with pytest.raises(KeyError, match="Input key not in schema"):
            memory.initialize_inputs({"invalid_key": "value"})

    def test_repr(self):
        """Test memory store string representation."""
        schema = MemorySchema(
            inputs={"in1": FieldDefinition(type="string")},
            outputs={"out1": FieldDefinition(type="string")},
            intermediate={"temp1": FieldDefinition(type="string")}
        )

        memory = MemoryStore(schema=schema)

        repr_str = repr(memory)

        assert "MemoryStore" in repr_str
        assert "inputs=0" in repr_str
        assert "outputs=" in repr_str
        assert "intermediate=" in repr_str
