import streamlit as st
from utils.connection.weaviate_client import initialize_client
from utils.cluster.cluster_operations_handlers import action_check_shard_consistency, action_aggregate_collections_tenants, action_collections_configuration, action_metadata, action_nodes_and_shards, action_collection_schema, action_statistics, action_read_repairs
from utils.sidebar.navigation import navigate
from utils.connection.weaviate_connection import close_weaviate_client
from utils.sidebar.helper import update_side_bar_labels, clear_session_state
from utils.page_config import set_custom_page_config
import time

# --------------------------------------------------------------------------
# Initialize session state
# --------------------------------------------------------------------------
if "client_ready" not in st.session_state:
	st.session_state.client_ready = False
if "use_local" not in st.session_state:
	st.session_state.use_local = False
if "use_custom" not in st.session_state:
	st.session_state.use_custom = False

# Local connection state
if "local_http_port" not in st.session_state:
	st.session_state.local_http_port = 8080
if "local_grpc_port" not in st.session_state:
	st.session_state.local_grpc_port = 50051
if "local_api_key" not in st.session_state:
	st.session_state.local_api_key = ""

# Custom connection state
if "custom_http_host" not in st.session_state:
	st.session_state.custom_http_host = "localhost"
if "custom_http_port" not in st.session_state:
	st.session_state.custom_http_port = 8080
if "custom_grpc_host" not in st.session_state:
	st.session_state.custom_grpc_host = "localhost"
if "custom_grpc_port" not in st.session_state:
	st.session_state.custom_grpc_port = 50051
if "custom_secure" not in st.session_state:
	st.session_state.custom_secure = False
if "custom_api_key" not in st.session_state:
	st.session_state.custom_api_key = ""

# Cloud connection state
if "cloud_endpoint" not in st.session_state:
	st.session_state.cloud_endpoint = ""
if "cloud_api_key" not in st.session_state:
	st.session_state.cloud_api_key = ""

# Vectorizer keys
if "openai_key" not in st.session_state:
	st.session_state.openai_key = ""
if "cohere_key" not in st.session_state:
	st.session_state.cohere_key = ""
if "jinaai_key" not in st.session_state:
	st.session_state.jinaai_key = ""
if "huggingface_key" not in st.session_state:
	st.session_state.huggingface_key = ""

# Azure OpenAI keys
if "azure_openai_api_key" not in st.session_state:
	st.session_state.azure_openai_api_key = ""
if "azure_openai_embedding_deployment" not in st.session_state:
	st.session_state.azure_openai_embedding_deployment = ""
if "azure_openai_resource_name" not in st.session_state:
	st.session_state.azure_openai_resource_name = ""
	
# Active connection state
if "active_endpoint" not in st.session_state:
	st.session_state.active_endpoint = ""
if "active_api_key" not in st.session_state:
	st.session_state.active_api_key = ""

# ------------------------ß--------------------------------------------------
# Streamlit Page Config
# --------------------------------------------------------------------------

# Use with default page title
set_custom_page_config()

# --------------------------------------------------------------------------
# Navigation on side bar
# --------------------------------------------------------------------------
navigate()

st.sidebar.title("✨Weaviate Connection✨")

if not st.session_state.client_ready:
	# Set the default value of connection type
	def local_checkbox_callback():
		if st.session_state.use_local:
			st.session_state.use_custom = False

	def custom_checkbox_callback():
		if st.session_state.use_custom:
			st.session_state.use_local = False

	# Connect to Weaviate
	use_local = st.sidebar.checkbox("Local", key='use_local', on_change=local_checkbox_callback)
	use_custom = st.sidebar.checkbox("Custom", key='use_custom', on_change=custom_checkbox_callback)

	# Conditional UI based on checkboxes
	if st.session_state.use_local:
		st.sidebar.markdown(
			'Clone the repository from [**Shah91n -> WeaviateCluster**](https://github.com/Shah91n/WeaviateCluster) GitHub and following the installation requirements. Then ensure that you have a local Weaviate instance running on your machine before attempting to connect.'
		)
		# This is now a display-only field, its value is derived from other state.
		# It does NOT have a key, which is critical to avoid state conflicts.
		st.sidebar.text_input(
			"Local Cluster Endpoint",
			value=f"http://localhost:{st.session_state.local_http_port}",
			disabled=True,
		)
		st.sidebar.number_input(
			"HTTP Port",
			value=st.session_state.local_http_port,
			key="local_http_port"
		)
		st.sidebar.number_input(
			"gRPC Port",
			value=st.session_state.local_grpc_port,
			key="local_grpc_port"
		)
		st.sidebar.text_input(
			"Local Cluster API Key",
			placeholder="Enter Cluster Admin Key",
			type="password",
			key="local_api_key"
		).strip()

	elif st.session_state.use_custom:
		st.sidebar.markdown(
			'Clone the repository from [**Shah91n -> WeaviateCluster**](https://github.com/Shah91n/WeaviateCluster) GitHub and following the installation requirements. Then ensure that you have a custom Weaviate instance running before attempting to connect.'
		)
		st.sidebar.text_input(
			"Custom HTTP Host",
			placeholder="e.g., localhost",
			key="custom_http_host"
		).strip()
		st.sidebar.number_input(
			"Custom HTTP Port",
			value=st.session_state.custom_http_port,
			key="custom_http_port"
		)
		st.sidebar.text_input(
			"Custom gRPC Host",
			placeholder="e.g., localhost",
			key="custom_grpc_host"
		).strip()
		st.sidebar.number_input(
			"Custom gRPC Port",
			value=st.session_state.custom_grpc_port,
			key="custom_grpc_port"
		)
		st.sidebar.checkbox(
			"Use Secure Connection (HTTPS/gRPC)",
			key="custom_secure"
		)
		st.sidebar.text_input(
			"Custom Cluster API Key",
			placeholder="Enter Cluster Admin Key",
			type="password",
			key="custom_api_key"
		).strip()

	else: # Cloud connection
		st.sidebar.markdown(
			'Connect to a Weaviate Cloud Cluster hosted by Weaviate. You can create clusters at [Weaviate Cloud](https://console.weaviate.cloud/).'
		)
		st.sidebar.text_input(
			"Cloud Cluster Endpoint",
			placeholder="Enter Cluster Endpoint (URL)",
			key="cloud_endpoint"
		).strip()
		st.sidebar.text_input(
			"Cloud Cluster API Key",
			placeholder="Enter Cluster Admin Key",
			type="password",
			key="cloud_api_key"
		).strip()

	# --------------------------------------------------------------------------
	# Vectorizers Integration API Keys Section
	# --------------------------------------------------------------------------
	st.sidebar.markdown("Add API keys for Model provider integrations (optional):")
	st.sidebar.text_input("OpenAI API Key", type="password", key="openai_key")
	st.sidebar.text_input("Cohere API Key", type="password", key="cohere_key")
	st.sidebar.text_input("JinaAI API Key", type="password", key="jinaai_key")
	st.sidebar.text_input("HuggingFace API Key", type="password", key="huggingface_key")
	
	# Azure OpenAI Configuration
	st.sidebar.markdown("Azure OpenAI Configuration (optional):")
	st.sidebar.text_input("Azure OpenAI API Key", type="password", key="azure_openai_api_key")
	st.sidebar.text_input("Azure OpenAI Embedding Deployment", key="azure_openai_embedding_deployment")
	st.sidebar.text_input("Azure OpenAI Resource Name", key="azure_openai_resource_name")

	# --------------------------------------------------------------------------
	# Connect/Disconnect Buttons
	# --------------------------------------------------------------------------
	if st.sidebar.button("Connect", use_container_width=True, type="secondary"):
		
		close_weaviate_client()

		# Vectorizers Integration API Keys
		vectorizer_integration_keys = {}
		if st.session_state.openai_key:
			vectorizer_integration_keys["X-OpenAI-Api-Key"] = st.session_state.openai_key
		if st.session_state.cohere_key:
			vectorizer_integration_keys["X-Cohere-Api-Key"] = st.session_state.cohere_key
		if st.session_state.jinaai_key:
			vectorizer_integration_keys["X-JinaAI-Api-Key"] = st.session_state.jinaai_key
		if st.session_state.huggingface_key:
			vectorizer_integration_keys["X-HuggingFace-Api-Key"] = st.session_state.huggingface_key
		
		# Azure OpenAI Configuration
		azure_openai_config = None
		if st.session_state.azure_openai_api_key or st.session_state.azure_openai_embedding_deployment or st.session_state.azure_openai_resource_name:
			azure_openai_config = {
				"api_key": st.session_state.azure_openai_api_key,
				"embedding_deployment": st.session_state.azure_openai_embedding_deployment,
				"resource_name": st.session_state.azure_openai_resource_name
			}

		if st.session_state.use_local:
			if initialize_client(
				use_local=True,
				http_port_endpoint=st.session_state.local_http_port,
				grpc_port_endpoint=st.session_state.local_grpc_port,
				cluster_api_key=st.session_state.local_api_key,
				vectorizer_integration_keys=vectorizer_integration_keys,
				azure_openai_config=azure_openai_config
			):
				st.sidebar.success("Local connection successful!")
				# Set active connection info
				st.session_state.active_endpoint = f"http://localhost:{st.session_state.local_http_port}"
				st.session_state.active_api_key = st.session_state.local_api_key
				# Persist the API keys in active_ keys
				for key in ["openai_key", "cohere_key", "jinaai_key", "huggingface_key", "azure_openai_api_key", "azure_openai_embedding_deployment", "azure_openai_resource_name"]:
					st.session_state[f"active_{key}"] = st.session_state.get(key, "")
				st.rerun()

			else:
				st.sidebar.error("Connection failed!")
		elif st.session_state.use_custom:
			if initialize_client(
				use_custom=True,
				http_host_endpoint=st.session_state.custom_http_host,
				http_port_endpoint=st.session_state.custom_http_port,
				grpc_host_endpoint=st.session_state.custom_grpc_host,
				grpc_port_endpoint=st.session_state.custom_grpc_port,
				custom_secure=st.session_state.custom_secure,
				cluster_api_key=st.session_state.custom_api_key,
				vectorizer_integration_keys=vectorizer_integration_keys,
				azure_openai_config=azure_openai_config
			):
				st.sidebar.success("Custom Connection successful!")
				# Set active connection info
				protocol = "https" if st.session_state.custom_secure else "http"
				st.session_state.active_endpoint = f"{protocol}://{st.session_state.custom_http_host}:{st.session_state.custom_http_port}"
				st.session_state.active_api_key = st.session_state.custom_api_key
				# Persist the API keys in active_ keys
				for key in ["openai_key", "cohere_key", "jinaai_key", "huggingface_key", "azure_openai_api_key", "azure_openai_embedding_deployment", "azure_openai_resource_name"]:
					st.session_state[f"active_{key}"] = st.session_state.get(key, "")
				st.rerun()
			else:
				st.sidebar.error("Connection failed!")
		else: # Cloud
			cloud_endpoint = st.session_state.cloud_endpoint
			if cloud_endpoint and not cloud_endpoint.startswith('https://'):
				cloud_endpoint = f"https://{cloud_endpoint}"

			if not cloud_endpoint or not st.session_state.cloud_api_key:
				st.sidebar.error("Please insert the cluster endpoint and API key!")
			else:
				if initialize_client(
					cluster_endpoint=cloud_endpoint,
					cluster_api_key=st.session_state.cloud_api_key,
					vectorizer_integration_keys=vectorizer_integration_keys,
					azure_openai_config=azure_openai_config
				):
					st.sidebar.success("Cloud Connection successful!")
					# Set active connection info
					st.session_state.active_endpoint = cloud_endpoint
					st.session_state.active_api_key = st.session_state.cloud_api_key
					# Persist the API keys in active_ keys
					for key in ["openai_key", "cohere_key", "jinaai_key", "huggingface_key"]:
						st.session_state[f"active_{key}"] = st.session_state.get(key, "")
					st.rerun()
				else:
					st.sidebar.error("Connection failed!")
	# print("DEBUG session_state (On Connect):", dict(st.session_state)) # uncomment during development to debug session state
else:
	if st.sidebar.button("Disconnect", use_container_width=True, type="primary"):
		st.toast('Session, states and cache cleared! Weaviate client disconnected successfully!', icon='🔴')
		time.sleep(1)
		if st.session_state.get("client_ready"):
			message = close_weaviate_client()
			clear_session_state()
			# print("DEBUG session_state (On Disconnect):", dict(st.session_state)) # uncomment during development to debug session state
	st.sidebar.info("Disconnect Button does clear all session states and cache, and disconnect the Weaviate client to server if connected.")

# Essential run for the first time
update_side_bar_labels()

# --------------------------------------------------------------------------
# Main Page Content (Cluster Operations)
# --------------------------------------------------------------------------
st.markdown("###### ⚠️ Important: This tool is designed and tested on the latest Weaviate DB version. Some features may not be compatible with older versions. Please ensure you are using the latest stable version of Weaviate DB for optimal performance.")
st.markdown("###### Any function with (APIs) means it is run using RESTful endpoints. Otherwise, it is executed through the DB client.")
# --------------------------------------------------------------------------
# Buttons (calls a function)
# --------------------------------------------------------------------------
col1, col2, col3 = st.columns([1, 1, 1])
col4, col5, col6 = st.columns([1, 1, 1])
col7, col8 = st.columns([1,1])

# Dictionary: button name => action function
button_actions = {
	"nodes": action_nodes_and_shards,
	"aggregate_collections_tenants": action_aggregate_collections_tenants,
	"collection_properties": action_collection_schema,
	"collections_configuration": lambda: action_collections_configuration(st.session_state.active_endpoint, st.session_state.active_api_key),
	"statistics": lambda: action_statistics(st.session_state.active_endpoint, st.session_state.active_api_key),
	"metadata": lambda: action_metadata(st.session_state.active_endpoint, st.session_state.active_api_key),
	"check_shard_consistency": action_check_shard_consistency,
	"read_repairs": lambda: action_read_repairs(st.session_state.active_endpoint, st.session_state.active_api_key),
}

with col1:
	if st.button("Aggregate Collections & Tenants", use_container_width=True):
		st.session_state["active_button"] = "aggregate_collections_tenants"

with col2:
	if st.button("Collection Properties", use_container_width=True):
		st.session_state["active_button"] = "collection_properties"

with col3:
	if st.button("Collections Configuration (APIs)", use_container_width=True):
		st.session_state["active_button"] = "collections_configuration"

with col4:
	if st.button("Nodes & Shards", use_container_width=True):
		st.session_state["active_button"] = "nodes"

with col5:
	if st.button("Raft Statistics (APIs)", use_container_width=True):
		st.session_state["active_button"] = "statistics"

with col6:
	if st.button("Metadata",use_container_width=True):
		st.session_state["active_button"] = "metadata"

with col7:
	if st.button("Check Shard Consistency For Repairs", use_container_width=True):
		st.session_state["active_button"] = "check_shard_consistency"

with col8:
	if st.button("Read Repair (APIs)", use_container_width=True):
		st.session_state["active_button"] = "read_repairs"

# --------------------------------------------------------------------------
# Execute the active button's action
# --------------------------------------------------------------------------
active_button = st.session_state.get("active_button")
if active_button and st.session_state.get("client_ready"):
	action_fn = button_actions.get(active_button)
	if action_fn:
		action_fn()
	else:
		st.warning("No action mapped for this button. Please report this issue to Mohamed Shahin in Weaviate Community Slack.")
elif not st.session_state.get("client_ready"):
	st.warning("Connect to Weaviate first!")
