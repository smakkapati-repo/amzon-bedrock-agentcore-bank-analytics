from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, Fargate, ECR, Lambda
from diagrams.aws.network import InternetGateway, ElasticLoadBalancing, VPC, APIGateway, NATGateway
from diagrams.aws.storage import S3
from diagrams.aws.ml import Bedrock
from diagrams.aws.management import Cloudwatch
from diagrams.aws.security import IAM
from diagrams.aws.general import User
from diagrams.onprem.client import Users as ExternalUsers
from diagrams.onprem.compute import Server
from diagrams.programming.language import Python, Javascript

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
    "BankIQ+ AgentCore Platform - AWS Architecture",
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
    
    with Cluster("Users", graph_attr={"bgcolor": "white", "style": "rounded"}):
        users = ExternalUsers("Banking Analysts\n& Executives")
        admin_users = User("Platform\nAdministrators")
    

    
    with Cluster("AWS Cloud - BankIQ+ Platform", graph_attr={"bgcolor": "white", "style": "rounded", "color": "#232F3E"}):
        
        # VPC
        with Cluster("VPC - Multi-AZ", graph_attr={"bgcolor": "white", "style": "rounded"}):
            
            igw = InternetGateway("Internet Gateway")
            
            # Public Subnets
            with Cluster("Public Subnets", graph_attr={"bgcolor": "white", "style": "rounded"}):
                alb = ElasticLoadBalancing("Application\nLoad Balancer")
                nat_gw = NATGateway("NAT Gateway")
            
            # Private Subnets
            with Cluster("Private Subnets", graph_attr={"bgcolor": "white", "style": "rounded"}):
                ui_fargate = Fargate("UI Container\nReact + Nginx")
                
            # NAT Gateway connection
            ui_fargate >> Edge(label="Internet Access", color="#9E9E9E", style="dashed") >> nat_gw
            
            # API Layer
            with Cluster("API Integration", graph_attr={"bgcolor": "white", "style": "rounded"}):
                api_gw = APIGateway("API Gateway")
                lambda_proxy = Lambda("Lambda Proxy\nAgentCore Integration")
            
            # Data Services
            with Cluster("Storage", graph_attr={"bgcolor": "white", "style": "rounded"}):
                s3_bucket = S3("S3 Bucket\nDocument Uploads")
        
        # AgentCore Runtime (External)
        with Cluster("Bedrock AgentCore", graph_attr={"bgcolor": "white", "style": "rounded"}):
            agentcore = Bedrock("AgentCore Runtime\nBanking Strands Agent")
            claude = Bedrock("Claude Sonnet 4.5\nAI Analysis")
            
        # Container Registry
        ecr_repo = ECR("ECR Repository\nUI Container")
        
        # Management & Security
        with Cluster("Management & Security", graph_attr={"bgcolor": "white", "style": "rounded"}):
            cloudwatch = Cloudwatch("CloudWatch\nLogs & Monitoring")
            iam = IAM("IAM Roles\nMinimal Permissions")
            
            cloudwatch - iam
    
    # Step 1: User Access
    users >> Edge(label="1. HTTPS Request\n(IP Restricted)", color="#FF9900", style="bold") >> igw >> alb
    admin_users >> Edge(label="Admin Access", color="#FF6B6B", style="dashed") >> igw >> alb
    
    # Step 2: Load Balancer to UI
    alb >> Edge(label="2. Route to UI", color="#4CAF50") >> ui_fargate
    
    # Step 3: UI to API Gateway
    ui_fargate >> Edge(label="3. API Calls", color="#2196F3") >> api_gw
    
    # Step 4: API Gateway to Lambda
    api_gw >> Edge(label="4. Proxy Request", color="#9C27B0") >> lambda_proxy
    
    # Step 5: Lambda to AgentCore
    lambda_proxy >> Edge(label="5. Invoke Agent", color="#FF5722") >> agentcore
    
    # Step 6: AgentCore to Claude
    agentcore >> Edge(label="6. AI Analysis", color="#E91E63") >> claude
    
    # Step 7: External Data (from AgentCore) - both arrows to the cluster
    agentcore >> Edge(label="7. Banking Data", color="#00BCD4") >> fdic_api
    agentcore >> Edge(label="8. SEC Filings", color="#00BCD4") >> fdic_api
    
    # Step 9: Document Storage
    ui_fargate >> Edge(label="9. File Uploads", color="#FF9800") >> s3_bucket
    
    # Container Deployment
    ecr_repo >> Edge(label="Deploy UI", color="#795548") >> ui_fargate
    
    # Infrastructure Services
    ui_fargate >> Edge(label="Logs & Metrics", color="#607D8B") >> cloudwatch
    lambda_proxy >> Edge(label="Permissions", color="#607D8B") >> iam