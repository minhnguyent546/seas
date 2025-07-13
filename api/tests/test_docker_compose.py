"""
Unit tests for Docker Compose configuration validation.

This test suite validates the Docker Compose configuration to ensure:
- All required services are defined
- Environment variables are properly configured
- Health checks are correctly set up
- Dependencies between services are properly defined
- Networks and volumes are configured correctly

Testing Framework: pytest
"""

import pytest
import yaml
import os
from pathlib import Path
from typing import Dict, Any


class TestDockerComposeConfiguration:
    """Test suite for validating Docker Compose configuration."""

    @pytest.fixture
    def docker_compose_config(self) -> Dict[str, Any]:
        """Load the Docker Compose configuration for testing."""
        compose_file = Path(__file__).parent.parent.parent / "docker-compose.yml"
        if not compose_file.exists():
            pytest.skip("docker-compose.yml not found in project root")
        
        with open(compose_file, 'r') as f:
            return yaml.safe_load(f)

    def test_all_required_services_present(self, docker_compose_config):
        """Test that all required services are defined in the composition."""
        required_services = ['db', 'adminer', 'api', 'ui']
        services = docker_compose_config.get('services', {})
        
        for service in required_services:
            assert service in services, f"Required service '{service}' not found in composition"
        
        assert len(services) == len(required_services), "Unexpected number of services defined"

    def test_database_service_configuration(self, docker_compose_config):
        """Test database service configuration comprehensively."""
        services = docker_compose_config.get('services', {})
        db_service = services.get('db', {})
        
        # Test image specification
        assert db_service.get('image') == 'postgres:17.5-bookworm', "Database image not correctly specified"
        
        # Test restart policy
        assert db_service.get('restart') == 'always', "Database restart policy should be 'always'"
        
        # Test health check configuration
        healthcheck = db_service.get('healthcheck', {})
        assert 'test' in healthcheck, "Database health check test not defined"
        assert 'interval' in healthcheck, "Database health check interval not defined"
        assert 'timeout' in healthcheck, "Database health check timeout not defined"
        assert 'retries' in healthcheck, "Database health check retries not defined"
        
        # Test health check values
        assert healthcheck.get('interval') == '10s', "Database health check interval should be 10s"
        assert healthcheck.get('timeout') == '5s', "Database health check timeout should be 5s"
        assert healthcheck.get('retries') == 3, "Database health check retries should be 3"
        
        # Test health check command
        health_test = healthcheck.get('test', [])
        assert isinstance(health_test, list), "Health check test should be a list"
        assert len(health_test) >= 2, "Health check test should have at least 2 elements"
        assert health_test[0] == "CMD-SHELL", "Health check should use CMD-SHELL"

    def test_database_environment_variables(self, docker_compose_config):
        """Test database environment variable configuration."""
        services = docker_compose_config.get('services', {})
        db_service = services.get('db', {})
        environment = db_service.get('environment', [])
        
        required_env_vars = [
            'PGDATA=/var/lib/postgresql/pgdata',
            'POSTGRES_DB=${POSTGRES_DB?Variable not set}',
            'POSTGRES_PASSWORD=${POSTGRES_PASSWORD?Variable not set}',
            'POSTGRES_USER=${POSTGRES_USER?Variable not set}'
        ]
        
        for env_var in required_env_vars:
            assert env_var in environment, f"Required environment variable '{env_var}' not found"
        
        # Test that PGDATA is correctly set
        pgdata_vars = [var for var in environment if var.startswith('PGDATA=')]
        assert len(pgdata_vars) == 1, "Exactly one PGDATA variable should be set"

    def test_database_volumes_configuration(self, docker_compose_config):
        """Test database volumes configuration."""
        services = docker_compose_config.get('services', {})
        db_service = services.get('db', {})
        volumes = db_service.get('volumes', [])
        
        assert 'seas-db-data:/var/lib/postgresql/pgdata' in volumes, "Database volume mapping not found"
        assert len(volumes) == 1, "Database should have exactly one volume mapping"

    def test_database_network_configuration(self, docker_compose_config):
        """Test database network configuration."""
        services = docker_compose_config.get('services', {})
        db_service = services.get('db', {})
        networks = db_service.get('networks', [])
        
        assert 'seas' in networks, "Database should be connected to 'seas' network"

    def test_adminer_service_configuration(self, docker_compose_config):
        """Test Adminer service configuration."""
        services = docker_compose_config.get('services', {})
        adminer_service = services.get('adminer', {})
        
        # Test image specification
        assert adminer_service.get('image') == 'adminer:5.3.0', "Adminer image not correctly specified"
        
        # Test restart policy
        assert adminer_service.get('restart') == 'always', "Adminer restart policy should be 'always'"
        
        # Test dependencies
        depends_on = adminer_service.get('depends_on', {})
        assert 'db' in depends_on, "Adminer should depend on database service"
        assert depends_on['db'].get('condition') == 'service_healthy', "Adminer should wait for database to be healthy"
        
        # Test environment configuration
        environment = adminer_service.get('environment', [])
        assert 'ADMINER_DESIGN=rmsoft' in environment, "Adminer should use rmsoft design"

    def test_api_service_configuration(self, docker_compose_config):
        """Test API service configuration."""
        services = docker_compose_config.get('services', {})
        api_service = services.get('api', {})
        
        # Test build configuration
        build = api_service.get('build', {})
        assert build.get('context') == 'api', "API build context should be 'api'"
        assert build.get('dockerfile') == 'Dockerfile', "API dockerfile should be 'Dockerfile'"
        
        # Test restart policy
        assert api_service.get('restart') == 'always', "API restart policy should be 'always'"
        
        # Test dependencies
        depends_on = api_service.get('depends_on', {})
        assert 'db' in depends_on, "API should depend on database service"
        assert depends_on['db'].get('condition') == 'service_healthy', "API should wait for database to be healthy"

    def test_api_environment_variables(self, docker_compose_config):
        """Test API service environment variables."""
        services = docker_compose_config.get('services', {})
        api_service = services.get('api', {})
        environment = api_service.get('environment', [])
        
        required_env_vars = [
            'API_PORT=8444',
            'POSTGRES_HOST=db',
            'POSTGRES_DB=${POSTGRES_DB?Variable not set}',
            'POSTGRES_PASSWORD=${POSTGRES_PASSWORD?Variable not set}',
            'POSTGRES_USER=${POSTGRES_USER?Variable not set}',
            'FIRST_USER_PASSWORD=${FIRST_USER_PASSWORD?Variable not set}'
        ]
        
        for env_var in required_env_vars:
            assert env_var in environment, f"Required environment variable '{env_var}' not found"

    def test_api_health_check(self, docker_compose_config):
        """Test API service health check configuration."""
        services = docker_compose_config.get('services', {})
        api_service = services.get('api', {})
        healthcheck = api_service.get('healthcheck', {})
        
        assert 'test' in healthcheck, "API health check test not defined"
        assert 'interval' in healthcheck, "API health check interval not defined"
        assert 'timeout' in healthcheck, "API health check timeout not defined"
        assert 'retries' in healthcheck, "API health check retries not defined"
        
        # Test health check values
        assert healthcheck.get('interval') == '10s', "API health check interval should be 10s"
        assert healthcheck.get('timeout') == '5s', "API health check timeout should be 5s"
        assert healthcheck.get('retries') == 3, "API health check retries should be 3"
        
        # Test health check command
        health_test = healthcheck.get('test', [])
        assert isinstance(health_test, list), "API health check test should be a list"
        assert 'curl -f http://localhost:8444/health' in ' '.join(health_test), "API health check should test /health endpoint"

    def test_ui_service_configuration(self, docker_compose_config):
        """Test UI service configuration."""
        services = docker_compose_config.get('services', {})
        ui_service = services.get('ui', {})
        
        # Test build configuration
        build = ui_service.get('build', {})
        assert build.get('context') == 'ui', "UI build context should be 'ui'"
        assert build.get('dockerfile') == 'Dockerfile', "UI dockerfile should be 'Dockerfile'"
        
        # Test build args
        args = build.get('args', [])
        assert 'NODE_ENV=production' in args, "UI should build with NODE_ENV=production"
        
        # Test restart policy
        assert ui_service.get('restart') == 'always', "UI restart policy should be 'always'"
        
        # Test dependencies
        depends_on = ui_service.get('depends_on', [])
        assert 'api' in depends_on, "UI should depend on API service"

    def test_networks_configuration(self, docker_compose_config):
        """Test networks configuration."""
        networks = docker_compose_config.get('networks', {})
        assert 'seas' in networks, "Required network 'seas' not found"
        
        # Check that all services are connected to the seas network
        services = docker_compose_config.get('services', {})
        for service_name, service_config in services.items():
            service_networks = service_config.get('networks', [])
            assert 'seas' in service_networks, f"Service '{service_name}' not connected to 'seas' network"

    def test_volumes_configuration(self, docker_compose_config):
        """Test volumes configuration."""
        volumes = docker_compose_config.get('volumes', {})
        assert 'seas-db-data' in volumes, "Required volume 'seas-db-data' not found"
        
        # Check that the volume is properly used by the database service
        services = docker_compose_config.get('services', {})
        db_service = services.get('db', {})
        db_volumes = db_service.get('volumes', [])
        volume_used = any('seas-db-data' in vol for vol in db_volumes)
        assert volume_used, "Volume 'seas-db-data' should be used by database service"

    def test_env_file_configuration(self, docker_compose_config):
        """Test that services requiring environment files have them configured."""
        services = docker_compose_config.get('services', {})
        
        # Database and API services should have env_file configured
        for service_name in ['db', 'api']:
            service = services.get(service_name, {})
            env_file = service.get('env_file', [])
            assert '.env' in env_file, f"Service '{service_name}' should have .env file configured"

    def test_service_startup_order(self, docker_compose_config):
        """Test that service dependencies create proper startup order."""
        services = docker_compose_config.get('services', {})
        
        # API should depend on database being healthy
        api_depends_on = services.get('api', {}).get('depends_on', {})
        assert 'db' in api_depends_on, "API should depend on database"
        assert api_depends_on['db'].get('condition') == 'service_healthy', "API should wait for database health"
        
        # Adminer should depend on database being healthy
        adminer_depends_on = services.get('adminer', {}).get('depends_on', {})
        assert 'db' in adminer_depends_on, "Adminer should depend on database"
        assert adminer_depends_on['db'].get('condition') == 'service_healthy', "Adminer should wait for database health"
        
        # UI should depend on API
        ui_depends_on = services.get('ui', {}).get('depends_on', [])
        assert 'api' in ui_depends_on, "UI should depend on API"

    def test_no_conflicting_ports(self, docker_compose_config):
        """Test that no services define conflicting port mappings."""
        services = docker_compose_config.get('services', {})
        used_ports = set()
        
        for service_name, service_config in services.items():
            ports = service_config.get('ports', [])
            for port_mapping in ports:
                if ':' in str(port_mapping):
                    host_port = str(port_mapping).split(':')[0]
                    assert host_port not in used_ports, f"Port conflict: {host_port} used by multiple services"
                    used_ports.add(host_port)

    def test_docker_compose_file_syntax(self, docker_compose_config):
        """Test that the Docker Compose file has valid YAML syntax and structure."""
        # If we got here, the YAML was parsed successfully
        assert isinstance(docker_compose_config, dict), "Docker Compose file should be a valid YAML dictionary"
        
        # Test top-level required sections
        assert 'services' in docker_compose_config, "Docker Compose file should have 'services' section"
        assert isinstance(docker_compose_config['services'], dict), "Services section should be a dictionary"
        
        # Test optional but expected sections
        assert 'networks' in docker_compose_config, "Docker Compose file should have 'networks' section"
        assert 'volumes' in docker_compose_config, "Docker Compose file should have 'volumes' section"

    def test_environment_variable_validation(self, docker_compose_config):
        """Test that required environment variables use proper validation syntax."""
        services = docker_compose_config.get('services', {})
        
        # Check for proper variable validation syntax
        validation_vars = ['POSTGRES_DB', 'POSTGRES_PASSWORD', 'POSTGRES_USER', 'FIRST_USER_PASSWORD']
        
        for service_name, service_config in services.items():
            environment = service_config.get('environment', [])
            for env_var in environment:
                for validation_var in validation_vars:
                    if f'{validation_var}=' in env_var and '${' in env_var:
                        assert '?Variable not set' in env_var, f"Environment variable {validation_var} in {service_name} should use validation syntax"

    def test_health_check_consistency(self, docker_compose_config):
        """Test that health checks are consistently configured across services."""
        services = docker_compose_config.get('services', {})
        
        # Services with health checks should have consistent timing
        services_with_healthcheck = ['db', 'api']
        
        for service_name in services_with_healthcheck:
            service = services.get(service_name, {})
            healthcheck = service.get('healthcheck', {})
            
            assert healthcheck.get('interval') == '10s', f"{service_name} health check interval should be 10s"
            assert healthcheck.get('timeout') == '5s', f"{service_name} health check timeout should be 5s"
            assert healthcheck.get('retries') == 3, f"{service_name} health check retries should be 3"

    def test_container_restart_policies(self, docker_compose_config):
        """Test that all services have appropriate restart policies."""
        services = docker_compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            restart_policy = service_config.get('restart')
            assert restart_policy == 'always', f"Service '{service_name}' should have restart policy 'always'"

    @pytest.mark.parametrize("service_name,expected_image", [
        ('db', 'postgres:17.5-bookworm'),
        ('adminer', 'adminer:5.3.0'),
    ])
    def test_service_images(self, docker_compose_config, service_name, expected_image):
        """Test that services use the correct container images."""
        services = docker_compose_config.get('services', {})
        service = services.get(service_name, {})
        
        assert service.get('image') == expected_image, f"Service '{service_name}' should use image '{expected_image}'"

    def test_build_services_configuration(self, docker_compose_config):
        """Test that build services are properly configured."""
        services = docker_compose_config.get('services', {})
        build_services = ['api', 'ui']
        
        for service_name in build_services:
            service = services.get(service_name, {})
            build_config = service.get('build', {})
            
            assert 'context' in build_config, f"Service '{service_name}' should have build context"
            assert 'dockerfile' in build_config, f"Service '{service_name}' should have dockerfile specified"
            assert build_config.get('dockerfile') == 'Dockerfile', f"Service '{service_name}' should use 'Dockerfile'"

    def test_postgres_specific_configuration(self, docker_compose_config):
        """Test PostgreSQL-specific configuration details."""
        services = docker_compose_config.get('services', {})
        db_service = services.get('db', {})
        
        # Test PostgreSQL version
        image = db_service.get('image', '')
        assert 'postgres:17.5' in image, "Should use PostgreSQL version 17.5"
        assert 'bookworm' in image, "Should use Debian Bookworm base image"
        
        # Test PostgreSQL data directory configuration
        environment = db_service.get('environment', [])
        pgdata_found = False
        for env_var in environment:
            if env_var.startswith('PGDATA='):
                assert env_var == 'PGDATA=/var/lib/postgresql/pgdata', "PGDATA should be set to custom location"
                pgdata_found = True
        assert pgdata_found, "PGDATA environment variable should be set"

    def test_api_port_configuration(self, docker_compose_config):
        """Test API port configuration."""
        services = docker_compose_config.get('services', {})
        api_service = services.get('api', {})
        environment = api_service.get('environment', [])
        
        # Check that API_PORT is set to 8444
        api_port_found = False
        for env_var in environment:
            if env_var.startswith('API_PORT='):
                assert env_var == 'API_PORT=8444', "API_PORT should be set to 8444"
                api_port_found = True
        assert api_port_found, "API_PORT environment variable should be set"

    def test_database_connection_configuration(self, docker_compose_config):
        """Test database connection configuration from API perspective."""
        services = docker_compose_config.get('services', {})
        api_service = services.get('api', {})
        environment = api_service.get('environment', [])
        
        # Check that POSTGRES_HOST points to the database service
        postgres_host_found = False
        for env_var in environment:
            if env_var.startswith('POSTGRES_HOST='):
                assert env_var == 'POSTGRES_HOST=db', "POSTGRES_HOST should point to 'db' service"
                postgres_host_found = True
        assert postgres_host_found, "POSTGRES_HOST environment variable should be set"

    def test_service_isolation_and_communication(self, docker_compose_config):
        """Test that services are properly isolated yet can communicate."""
        services = docker_compose_config.get('services', {})
        
        # All services should be on the same network for communication
        for service_name, service_config in services.items():
            networks = service_config.get('networks', [])
            assert 'seas' in networks, f"Service '{service_name}' should be on 'seas' network for communication"
        
        # No services should expose ports to host (security check)
        for service_name, service_config in services.items():
            ports = service_config.get('ports', [])
            assert len(ports) == 0, f"Service '{service_name}' should not expose ports to host for security"

    def test_ui_production_build(self, docker_compose_config):
        """Test that UI service is configured for production deployment."""
        services = docker_compose_config.get('services', {})
        ui_service = services.get('ui', {})
        build = ui_service.get('build', {})
        args = build.get('args', [])
        
        # Check for production build configuration
        assert 'NODE_ENV=production' in args, "UI should be built with NODE_ENV=production"

    def test_critical_failure_scenarios(self, docker_compose_config):
        """Test configuration handles critical failure scenarios."""
        services = docker_compose_config.get('services', {})
        
        # Test that database has proper health checks for critical failures
        db_service = services.get('db', {})
        healthcheck = db_service.get('healthcheck', {})
        assert healthcheck.get('retries') == 3, "Database should retry health checks 3 times"
        
        # Test that API waits for database health before starting
        api_service = services.get('api', {})
        depends_on = api_service.get('depends_on', {})
        assert depends_on.get('db', {}).get('condition') == 'service_healthy', "API should wait for healthy database"

    def test_edge_cases_and_error_conditions(self, docker_compose_config):
        """Test edge cases and error conditions in configuration."""
        # Test that configuration doesn't have empty or null values where they shouldn't be
        services = docker_compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            # No service should be empty
            assert service_config, f"Service '{service_name}' configuration should not be empty"
            
            # Required fields should not be None
            if 'image' in service_config:
                assert service_config['image'], f"Service '{service_name}' image should not be empty"
            if 'build' in service_config:
                assert service_config['build'], f"Service '{service_name}' build config should not be empty"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])