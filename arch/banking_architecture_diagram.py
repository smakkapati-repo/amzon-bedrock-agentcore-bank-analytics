from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, Fargate, ECR
from diagrams.aws.network import InternetGateway, ElasticLoadBalancing, VPC, CloudFront
from diagrams.aws.storage import S3
from diagrams.aws.ml import Bedrock
from diagrams.aws.management import Cloudwatch
from diagrams.aws.security import IAM
from diagrams.aws.general import User
from diagrams.onprem.client import Users as ExternalUsers
from diagrams.onprem.compute import Server

# AWS-style professional configuration
graph_attr = {
    "fontsize": "14",
    "fontname": "Amazon Ember, Arial, sans-serif",
    "bgcolor": "#FFFFFF",
    "pad": "0.5",
    "splines": "ortho",
    "nodesep": "0.8",
    "ranksep": "1.2",
    "compound": "true"
}

node_attr = {
    "fontsize": "11",
    "fontname": "Amazon Ember, Arial, sans-serif",
    "style": "",
    "fillcolor": "none",
    "color": "#232F3E"
}

edge_attr = {
    "fontsize": "9",
    "fontname": "Amazon Ember, Arial, sans-serif",
    "color": "#232F3E"
}

with Diagram(
    "BankIQ+ Production Architecture - CloudFront + ECS + AgentCore",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
    filename="bankiq_plus_agentcore_architecture"
):
    
    with Cluster("External Data Sources", graph_attr={"bgcolor": "white", "style": "rounded", "rankdir": "LR"}):
        fdic_api = Server("FDIC Call Reports\n2024-2025 Data")
        sec_api = Server("SEC EDGAR API\nLive Filings")
        
        fdic_api - sec_api
    
    users = ExternalUsers("Banking Analysts\n& Executives")
    

    
    with Cluster("AWS Cloud - BankIQ+ Platform", graph_attr={"bgcolor": "white", "style": "rounded", "color": "#232F3E"}):
        
        # CloudFront CDN
        cloudfront = CloudFront("CloudFront CDN\n300s Timeout")
        
        # Frontend Storage
        with Cluster("Frontend", graph_attr={"bgcolor": "white", "style": "rounded"}):
            s3_frontend = S3("S3 Bucket\nReact App (Static)")
        
        # VPC
        with Cluster("VPC - Multi-AZ", graph_attr={"bgcolor": "white", "style": "rounded"}):
            
            # Public Subnets
            with Cluster("Public Subnets", graph_attr={"bgcolor": "white", "style": "rounded"}):
                alb = ElasticLoadBalancing("Application\nLoad Balancer\n300s Timeout")
            
            # Private Subnets
            with Cluster("Private Subnets - ECS Fargate", graph_attr={"bgcolor": "white", "style": "rounded"}):
                ecs_backend = Fargate("Backend Container\nNode.js Express\n12 AI Tools")
            
            # Data Services
            with Cluster("Storage", graph_attr={"bgcolor": "white", "style": "rounded"}):
                s3_docs = S3("S3 Bucket\nUploaded Documents")
        
        # AgentCore Runtime
        with Cluster("Bedrock AgentCore", graph_attr={"bgcolor": "white", "style": "rounded"}):
            agentcore = Bedrock("AgentCore Runtime\nbank_iq_agent_v1\n12 Tools + Memory")
            claude = Bedrock("Claude Sonnet 4.5\nConversational AI")
            
        # Container Registry
        ecr_repo = ECR("ECR Repository\nBackend Image")
        
        # Management & Security
        with Cluster("Management & Security", graph_attr={"bgcolor": "white", "style": "rounded"}):
            cloudwatch = Cloudwatch("CloudWatch\nLogs & Monitoring")
            iam = IAM("IAM Roles\nMinimal Permissions")
            
            cloudwatch - iam
    
    # Step 1: User to CloudFront
    users >> Edge(label="1. HTTPS Request", color="#FF9900", style="bold") >> cloudfront
    
    # Step 2: CloudFront to S3 (static files)
    cloudfront >> Edge(label="2a. Static Files\n(/, /static/*)", color="#4CAF50") >> s3_frontend
    
    # Step 3: CloudFront to ALB (API calls)
    cloudfront >> Edge(label="2b. API Calls\n(/api/*, HTTP)", color="#2196F3") >> alb
    
    # Step 4: ALB to ECS Backend
    alb >> Edge(label="3. Route to Backend", color="#9C27B0") >> ecs_backend
    
    # Step 5: Backend to AgentCore
    ecs_backend >> Edge(label="4. Invoke Agent\n(HTTPS + SigV4)", color="#FF5722") >> agentcore
    
    # Step 6: AgentCore to Claude
    agentcore >> Edge(label="5. AI Analysis", color="#E91E63") >> claude
    
    # Step 7: External Data
    agentcore >> Edge(label="6a. FDIC Data", color="#00BCD4") >> fdic_api
    agentcore >> Edge(label="6b. SEC Filings", color="#00BCD4") >> sec_api
    
    # Step 8: Document Storage
    ecs_backend >> Edge(label="7. Upload Docs", color="#FF9800") >> s3_docs
    agentcore >> Edge(label="8. Read Docs", color="#FF9800", style="dashed") >> s3_docs
    
    # Container Deployment
    ecr_repo >> Edge(label="Deploy Backend", color="#795548") >> ecs_backend
    
    # Infrastructure Services
    ecs_backend >> Edge(label="Logs & Metrics", color="#607D8B") >> cloudwatch
    agentcore >> Edge(label="Logs & Traces", color="#607D8B") >> cloudwatch
    ecs_backend >> Edge(label="IAM Permissions", color="#607D8B", style="dashed") >> iam