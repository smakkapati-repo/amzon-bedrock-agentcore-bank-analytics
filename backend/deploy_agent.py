#!/usr/bin/env python3
"""
Deploy banking agent to AgentCore Runtime
"""

import uuid
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

def main():
    # Initialize AWS session
    boto_session = Session()
    region = boto_session.region_name
    
    print(f"Deploying to region: {region}")
    
    # Initialize AgentCore Runtime
    agentcore_runtime = Runtime()
    
    agent_name = "banking_strands_agent"
    
    print("Configuring AgentCore Runtime...")
    response = agentcore_runtime.configure(
        entrypoint="banking_strands_agent.py",
        auto_create_execution_role=True,
        auto_create_ecr=True,
        requirements_file="requirements.txt",
        region=region,
        agent_name=agent_name,
    )
    
    print("Configuration completed ✓")
    
    print("Launching Agent to AgentCore Runtime...")
    print("This may take several minutes...")
    
    launch_result = agentcore_runtime.launch(
        env_vars={"OTEL_PYTHON_EXCLUDED_URLS": "/ping,/invocations"}
    )
    
    print("Launch completed ✓")
    print(f"Agent ARN: {launch_result.agent_arn}")
    print(f"Agent ID: {launch_result.agent_id}")
    
    # Save deployment info
    with open("deployment_info.txt", "w") as f:
        f.write(f"Agent ARN: {launch_result.agent_arn}\n")
        f.write(f"Agent ID: {launch_result.agent_id}\n")
        f.write(f"ECR URI: {launch_result.ecr_uri}\n")
    
    print("Deployment info saved to deployment_info.txt")
    
    return launch_result

if __name__ == "__main__":
    result = main()