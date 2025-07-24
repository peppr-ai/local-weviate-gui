import streamlit as st
from utils.connection.weaviate_connection import get_weaviate_client, status

# Initializes the Weaviate client and sets the session state variables.
def initialize_client(
	cluster_endpoint=None, 
	cluster_api_key=None, 
	use_local=False, 
	vectorizer_integration_keys=None, 
	use_custom=False, 
	http_host_endpoint=None, 
	http_port_endpoint=None, 
	grpc_host_endpoint=None, 
	grpc_port_endpoint=None, 
	custom_secure=False,
	azure_openai_config=None
):
	print("initialize_client() called")
	try:
		client = get_weaviate_client(
			cluster_endpoint=cluster_endpoint,
			cluster_api_key=cluster_api_key,
			use_local=use_local,
			vectorizer_integration_keys=vectorizer_integration_keys,
			use_custom=use_custom,
			http_host_endpoint=http_host_endpoint,
			http_port_endpoint=http_port_endpoint,
			grpc_host_endpoint=grpc_host_endpoint,
			grpc_port_endpoint=grpc_port_endpoint,
			custom_secure=custom_secure,
			azure_openai_config=azure_openai_config
		)
		st.session_state.client = client
		ready, server_version, client_version = status(client)
		st.session_state.client_ready = ready
		st.session_state.server_version = server_version
		st.session_state.client_version = client_version
		return True
	except Exception as e:
		st.sidebar.error(f"Connection Error: {e}")
		st.session_state.client = None
		st.session_state.client_ready = False
		return False
