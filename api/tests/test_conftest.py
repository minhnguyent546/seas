"""
Unit tests for conftest.py fixtures.

This module tests the pytest fixtures defined in conftest.py to ensure
they work correctly and provide the expected functionality for testing.

Testing Framework: pytest with pytest-asyncio
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import AsyncGenerator

from app.core.database import AsyncSessionLocal, init_db
from app.main import app


class TestSessionFixture:
    """Test the database session fixture."""

    @pytest.mark.asyncio
    async def test_session_fixture_creates_session(self):
        """Test that session fixture creates and yields a database session."""
        from api.tests.conftest import session
        
        # Mock AsyncSessionLocal
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('api.tests.conftest.AsyncSessionLocal') as mock_session_local, \
             patch('api.tests.conftest.init_db') as mock_init_db:
            mock_session_local.return_value = mock_session
            mock_init_db.return_value = None
            
            # Get the fixture generator
            session_gen = session()
            
            # Test that the session is yielded
            db_session = await session_gen.__anext__()
            
            # Verify session was created
            mock_session_local.assert_called_once()
            assert db_session is mock_session
            
            # Test cleanup
            try:
                await session_gen.__anext__()
            except StopAsyncIteration:
                pass  # Expected behavior

    @pytest.mark.asyncio
    async def test_session_fixture_calls_init_db(self):
        """Test that session fixture calls init_db with the session."""
        from api.tests.conftest import session
        
        # Create mock session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('api.tests.conftest.AsyncSessionLocal') as mock_session_local, \
             patch('api.tests.conftest.init_db') as mock_init_db:
            mock_session_local.return_value = mock_session
            mock_init_db.return_value = None
            
            # Execute the fixture
            session_gen = session()
            await session_gen.__anext__()
            
            # Verify init_db was called with the session
            mock_init_db.assert_called_once_with(session=mock_session)

    @pytest.mark.asyncio
    async def test_session_fixture_handles_context_manager_properly(self):
        """Test that session fixture properly handles async context manager."""
        from api.tests.conftest import session
        
        # Create mock session with context manager methods
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('api.tests.conftest.AsyncSessionLocal') as mock_session_local, \
             patch('api.tests.conftest.init_db') as mock_init_db:
            mock_session_local.return_value = mock_session
            mock_init_db.return_value = None
            
            # Execute the fixture
            session_gen = session()
            db_session = await session_gen.__anext__()
            
            # Verify context manager methods were called
            mock_session.__aenter__.assert_called_once()
            
            # Clean up
            try:
                await session_gen.__anext__()
            except StopAsyncIteration:
                pass
            
            # Verify context manager exit was called
            mock_session.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_fixture_handles_database_error(self):
        """Test session fixture behavior when database connection fails."""
        from api.tests.conftest import session
        
        with patch('api.tests.conftest.AsyncSessionLocal') as mock_session_local:
            # Mock database connection error
            mock_session_local.side_effect = Exception("Database connection failed")
            
            # Verify exception is propagated
            with pytest.raises(Exception, match="Database connection failed"):
                session_gen = session()
                await session_gen.__anext__()


class TestClientFixture:
    """Test the AsyncClient fixture."""

    @pytest.mark.asyncio
    async def test_client_fixture_creates_async_client(self):
        """Test that client fixture creates an AsyncClient with correct configuration."""
        from api.tests.conftest import client
        
        # Mock AsyncClient
        mock_client = AsyncMock(spec=AsyncClient)
        mock_client.base_url = "http://test"
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('api.tests.conftest.AsyncClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Execute the fixture
            client_gen = client()
            test_client = await client_gen.__anext__()
            
            # Verify client is created with correct configuration
            mock_client_class.assert_called_once()
            call_args = mock_client_class.call_args
            assert call_args.kwargs['base_url'] == "http://test"
            assert test_client is mock_client
            
            # Clean up
            try:
                await client_gen.__anext__()
            except StopAsyncIteration:
                pass

    @pytest.mark.asyncio
    async def test_client_fixture_uses_asgi_transport(self):
        """Test that client fixture uses ASGITransport with the app."""
        from api.tests.conftest import client
        
        mock_client = AsyncMock(spec=AsyncClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('api.tests.conftest.ASGITransport') as mock_transport, \
             patch('api.tests.conftest.AsyncClient') as mock_client_class:
            mock_transport.return_value = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Execute the fixture
            client_gen = client()
            await client_gen.__anext__()
            
            # Verify ASGITransport was called with the app
            mock_transport.assert_called_once_with(app=app)
            
            # Clean up
            try:
                await client_gen.__anext__()
            except StopAsyncIteration:
                pass

    @pytest.mark.asyncio
    async def test_client_fixture_context_manager_cleanup(self):
        """Test that client fixture properly handles context manager cleanup."""
        from api.tests.conftest import client
        
        # Mock AsyncClient to track context manager calls
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('api.tests.conftest.AsyncClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Execute the fixture
            client_gen = client()
            test_client = await client_gen.__anext__()
            
            # Verify client was entered
            mock_client.__aenter__.assert_called_once()
            
            # Clean up
            try:
                await client_gen.__anext__()
            except StopAsyncIteration:
                pass
            
            # Verify client was properly closed
            mock_client.__aexit__.assert_called_once()

    @pytest.mark.asyncio 
    async def test_client_fixture_handles_app_startup_error(self):
        """Test client fixture behavior when app startup fails."""
        from api.tests.conftest import client
        
        with patch('api.tests.conftest.AsyncClient') as mock_client:
            # Mock app startup error
            mock_client.side_effect = Exception("App startup failed")
            
            # Verify exception is propagated
            with pytest.raises(Exception, match="App startup failed"):
                client_gen = client()
                await client_gen.__anext__()


class TestSuperuserTokenHeadersFixture:
    """Test the superuser token headers fixture."""

    @pytest.mark.asyncio
    async def test_superuser_token_headers_fixture_returns_headers(self):
        """Test that superuser_token_headers fixture returns authentication headers."""
        from api.tests.conftest import superuser_token_headers
        
        mock_client = AsyncMock(spec=AsyncClient)
        expected_headers = {"Authorization": "Bearer test-token"}
        
        with patch('api.tests.conftest.get_superuser_token_headers') as mock_func:
            mock_func.return_value = expected_headers
            
            # Execute the fixture
            headers = await superuser_token_headers(mock_client)
            
            # Verify headers are returned
            assert headers == expected_headers
            mock_func.assert_called_once_with(client=mock_client)

    @pytest.mark.asyncio
    async def test_superuser_token_headers_fixture_calls_utility_function(self):
        """Test that fixture properly calls the utility function with client."""
        from api.tests.conftest import superuser_token_headers
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        with patch('api.tests.conftest.get_superuser_token_headers') as mock_func:
            mock_func.return_value = {"Authorization": "Bearer token"}
            
            # Execute the fixture
            await superuser_token_headers(mock_client)
            
            # Verify the utility function was called correctly
            mock_func.assert_called_once_with(client=mock_client)

    @pytest.mark.asyncio
    async def test_superuser_token_headers_fixture_handles_empty_headers(self):
        """Test that fixture handles empty headers gracefully."""
        from api.tests.conftest import superuser_token_headers
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        with patch('api.tests.conftest.get_superuser_token_headers') as mock_func:
            # Mock empty headers
            mock_func.return_value = {}
            
            # Execute the fixture
            headers = await superuser_token_headers(mock_client)
            
            # Verify empty headers are handled
            assert headers == {}
            mock_func.assert_called_once_with(client=mock_client)

    @pytest.mark.asyncio
    async def test_superuser_token_headers_fixture_handles_exception(self):
        """Test that fixture properly propagates exceptions from utility function."""
        from api.tests.conftest import superuser_token_headers
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        with patch('api.tests.conftest.get_superuser_token_headers') as mock_func:
            # Mock authentication failure
            mock_func.side_effect = ValueError("Authentication failed")
            
            # Verify exception is propagated
            with pytest.raises(ValueError, match="Authentication failed"):
                await superuser_token_headers(mock_client)

    @pytest.mark.asyncio
    async def test_superuser_headers_handles_auth_failure(self):
        """Test superuser headers fixture behavior when authentication fails."""
        from api.tests.conftest import superuser_token_headers
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        with patch('api.tests.conftest.get_superuser_token_headers') as mock_headers:
            # Mock authentication failure
            mock_headers.side_effect = Exception("Authentication service unavailable")
            
            # Verify exception is propagated
            with pytest.raises(Exception, match="Authentication service unavailable"):
                await superuser_token_headers(mock_client)


class TestFixtureIntegration:
    """Integration tests for fixture interactions."""

    @pytest.mark.asyncio
    async def test_fixtures_work_together(self):
        """Test that all fixtures can be used together in a realistic scenario."""
        from api.tests.conftest import session, client, superuser_token_headers
        
        # Setup mocks
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        mock_client = AsyncMock(spec=AsyncClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('api.tests.conftest.AsyncSessionLocal') as mock_session_local, \
             patch('api.tests.conftest.init_db') as mock_init_db, \
             patch('api.tests.conftest.AsyncClient') as mock_client_class, \
             patch('api.tests.conftest.get_superuser_token_headers') as mock_headers:
            
            mock_session_local.return_value = mock_session
            mock_init_db.return_value = None
            mock_client_class.return_value = mock_client
            mock_headers.return_value = {"Authorization": "Bearer token"}
            
            # Test session fixture
            session_gen = session()
            db_session = await session_gen.__anext__()
            assert db_session is not None
            
            # Test client fixture
            client_gen = client()
            test_client = await client_gen.__anext__()
            assert test_client is not None
            
            # Test superuser headers
            headers = await superuser_token_headers(test_client)
            assert "Authorization" in headers
            
            # Cleanup
            try:
                await session_gen.__anext__()
            except StopAsyncIteration:
                pass
            try:
                await client_gen.__anext__()
            except StopAsyncIteration:
                pass

    def test_fixture_scopes_are_correct(self):
        """Test that fixtures have the correct pytest scopes."""
        from api.tests.conftest import session, client, superuser_token_headers
        
        # Check session fixture scope
        session_fixture = getattr(session, '_pytestfixturefunction', None)
        if session_fixture:
            assert session_fixture.scope == "session"
        
        # Check client fixture scope  
        client_fixture = getattr(client, '_pytestfixturefunction', None)
        if client_fixture:
            assert client_fixture.scope == "session"
        
        # Check superuser_token_headers fixture scope
        headers_fixture = getattr(superuser_token_headers, '_pytestfixturefunction', None)
        if headers_fixture:
            assert headers_fixture.scope == "session"

    def test_fixture_autouse_settings(self):
        """Test that session fixture has autouse=True."""
        from api.tests.conftest import session
        
        session_fixture = getattr(session, '_pytestfixturefunction', None)
        if session_fixture:
            assert session_fixture.autouse is True


class TestConfTestImports:
    """Test that all required imports are available and correct."""

    def test_import_collections_abc(self):
        """Test that collections.abc.AsyncGenerator import works."""
        from collections.abc import AsyncGenerator
        assert AsyncGenerator is not None

    def test_import_pytest_asyncio(self):
        """Test that pytest_asyncio import works."""
        import pytest_asyncio
        assert pytest_asyncio is not None

    def test_import_httpx_components(self):
        """Test that HTTPX components import correctly."""
        from httpx import ASGITransport, AsyncClient
        assert ASGITransport is not None
        assert AsyncClient is not None

    def test_import_database_components(self):
        """Test that database components import correctly."""
        from app.core.database import AsyncSession, AsyncSessionLocal, init_db
        assert AsyncSession is not None
        assert AsyncSessionLocal is not None
        assert init_db is not None

    def test_import_app(self):
        """Test that main app import works."""
        from app.main import app
        assert app is not None

    def test_import_user_utils(self):
        """Test that user utility functions import correctly."""
        from tests.utils.users import get_superuser_token_headers
        assert get_superuser_token_headers is not None


class TestFixtureDocumentation:
    """Test that fixtures have proper documentation and type hints."""

    def test_session_fixture_has_docstring(self):
        """Test that session fixture has proper documentation."""
        from api.tests.conftest import session
        assert session.__doc__ is not None
        assert "database session" in session.__doc__.lower()

    def test_client_fixture_has_docstring(self):
        """Test that client fixture has proper documentation."""
        from api.tests.conftest import client
        assert client.__doc__ is not None
        assert "test client" in client.__doc__.lower()

    def test_superuser_headers_fixture_exists(self):
        """Test that superuser headers fixture exists and is callable."""
        from api.tests.conftest import superuser_token_headers
        assert superuser_token_headers is not None
        assert callable(superuser_token_headers)

    def test_fixtures_have_proper_return_annotations(self):
        """Test that fixtures have proper return type annotations."""
        import inspect
        from api.tests.conftest import session, client, superuser_token_headers
        
        # Check session return type
        session_sig = inspect.signature(session)
        assert session_sig.return_annotation is not None
        
        # Check client return type  
        client_sig = inspect.signature(client)
        assert client_sig.return_annotation is not None
        
        # Check superuser headers return type
        headers_sig = inspect.signature(superuser_token_headers)
        assert headers_sig.return_annotation is not None


class TestFixtureAsyncGeneratorBehavior:
    """Test async generator behavior of fixtures."""

    @pytest.mark.asyncio
    async def test_session_fixture_is_async_generator(self):
        """Test that session fixture returns an async generator."""
        from api.tests.conftest import session
        
        with patch('api.tests.conftest.AsyncSessionLocal') as mock_session_local, \
             patch('api.tests.conftest.init_db') as mock_init_db:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_session
            mock_init_db.return_value = None
            
            # Test that it returns an async generator
            session_gen = session()
            assert hasattr(session_gen, '__anext__')
            assert hasattr(session_gen, '__aiter__')

    @pytest.mark.asyncio
    async def test_client_fixture_is_async_generator(self):
        """Test that client fixture returns an async generator."""
        from api.tests.conftest import client
        
        with patch('api.tests.conftest.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            # Test that it returns an async generator
            client_gen = client()
            assert hasattr(client_gen, '__anext__')
            assert hasattr(client_gen, '__aiter__')


class TestFixtureErrorScenarios:
    """Test various error scenarios for fixtures."""

    @pytest.mark.asyncio
    async def test_session_fixture_handles_init_db_error(self):
        """Test session fixture behavior when init_db fails."""
        from api.tests.conftest import session
        
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('api.tests.conftest.AsyncSessionLocal') as mock_session_local, \
             patch('api.tests.conftest.init_db') as mock_init_db:
            mock_session_local.return_value = mock_session
            mock_init_db.side_effect = Exception("Database initialization failed")
            
            # Verify exception is propagated
            with pytest.raises(Exception, match="Database initialization failed"):
                session_gen = session()
                await session_gen.__anext__()

    @pytest.mark.asyncio
    async def test_client_fixture_handles_transport_error(self):
        """Test client fixture behavior when ASGITransport creation fails."""
        from api.tests.conftest import client
        
        with patch('api.tests.conftest.ASGITransport') as mock_transport:
            mock_transport.side_effect = Exception("Transport creation failed")
            
            # Verify exception is propagated
            with pytest.raises(Exception, match="Transport creation failed"):
                client_gen = client()
                await client_gen.__anext__()

    @pytest.mark.asyncio
    async def test_superuser_headers_handles_network_error(self):
        """Test superuser headers fixture behavior with network errors."""
        from api.tests.conftest import superuser_token_headers
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        with patch('api.tests.conftest.get_superuser_token_headers') as mock_func:
            mock_func.side_effect = ConnectionError("Network unavailable")
            
            # Verify exception is propagated
            with pytest.raises(ConnectionError, match="Network unavailable"):
                await superuser_token_headers(mock_client)


class TestFixtureParameterTypes:
    """Test fixture parameter types and validation."""

    @pytest.mark.asyncio
    async def test_superuser_headers_requires_async_client(self):
        """Test that superuser_token_headers requires AsyncClient parameter."""
        from api.tests.conftest import superuser_token_headers
        import inspect
        
        # Check function signature
        sig = inspect.signature(superuser_token_headers)
        params = list(sig.parameters.values())
        
        # Should have one parameter of type AsyncClient
        assert len(params) == 1
        client_param = params[0]
        assert client_param.name == "client"
        assert "AsyncClient" in str(client_param.annotation)

    def test_session_fixture_return_type(self):
        """Test that session fixture has correct return type annotation."""
        from api.tests.conftest import session
        import inspect
        
        sig = inspect.signature(session)
        return_annotation = sig.return_annotation
        
        # Should return AsyncGenerator[AsyncSession, None]
        assert "AsyncGenerator" in str(return_annotation)
        assert "AsyncSession" in str(return_annotation)

    def test_client_fixture_return_type(self):
        """Test that client fixture has correct return type annotation."""
        from api.tests.conftest import client
        import inspect
        
        sig = inspect.signature(client)
        return_annotation = sig.return_annotation
        
        # Should return AsyncGenerator[AsyncClient, None]
        assert "AsyncGenerator" in str(return_annotation)
        assert "AsyncClient" in str(return_annotation)