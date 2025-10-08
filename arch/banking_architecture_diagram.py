from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, Fargate, ECR
from diagrams.aws.network import InternetGateway, ElasticLoadBalancing, VPC
from diagrams.aws.storage import S3
from diagrams.aws.devtools import Codebuild
from diagrams.aws.ml import Bedrock
from diagrams.aws.management import Cloudwatch, SystemsManager
from diagrams.aws.security import IAM, SecretsManager
from diagrams.aws.general import User, Users, Client
from diagrams.aws.general import General
from diagrams.aws.database import Dynamodb
from diagrams.onprem.client import Users as ExternalUsers
from diagrams.generic.network import Firewall
from diagrams.generic.database import SQL
from diagrams.aws.network import APIGateway as APIGatewayIcon
from diagrams.aws.analytics import Quicksight
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
    "style": "filled",
    "fillcolor": "#FFFFFF",
    "color": "#232F3E"
}

edge_attr = {
    "fontsize": "9",
    "fontname": "Amazon Ember, Arial, sans-serif",
    "color": "#232F3E"
}

with Diagram(
    "Banking Peer Analytics Platform - AWS Architecture",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
    filename="banking_peer_analytics_architecture"
):
    
    # External entities
    internet = Client("Internet")
    
    with Cluster("External Data Sources", graph_attr={"bgcolor": "#E3F2FD", "style": "rounded"}):
        fdic_api = APIGatewayIcon("FDIC APIs\nReal-time Banking Data")
        sec_api = Quicksight("SEC EDGAR APIs\nFinancial Reports")
    
    with Cluster("Users", graph_attr={"bgcolor": "#FFF9C4", "style": "rounded"}):
        users = ExternalUsers("Banking Analysts\n& Executives")
        admin_users = User("System Administrators")
    
    # AWS Cloud boundary
    aws_cloud = General("AWS Cloud")
    
    with Cluster("AWS Cloud Services", graph_attr={"bgcolor": "#F0F8FF", "style": "rounded", "color": "#232F3E"}):
        
        # VPC
        with Cluster("VPC - us-east-1", graph_attr={"bgcolor": "#E1F5FE", "style": "rounded"}):
            
            # Internet Gateway
            igw = InternetGateway("Internet Gateway")
            
            # Public Subnet
            with Cluster("Public Subnet", graph_attr={"bgcolor": "#B3E5FC", "style": "rounded"}):
                alb = ElasticLoadBalancing("Application\nLoad Balancer")
                
                # ECS Fargate Services
                with Cluster("ECS Fargate Cluster", graph_attr={"bgcolor": "#FFFFFF", "style": "rounded"}):
                    ecs_cluster = ECS("ECS Cluster\npeer-bank-analytics")
                    fargate_service = Fargate("Fargate Service\nReact + Flask App")
                    container_app = Python("Container\nReact + Flask API")
                
                # AI/ML Services
                with Cluster("AI/ML Services", graph_attr={"bgcolor": "#F3E5F5", "style": "rounded"}):
                    bedrock = Bedrock("Amazon Bedrock\nClaude 3.5 Sonnet")
                    vector_db = Dynamodb("Vector Store\nFAISS Embeddings")
                
                # Data Services
                with Cluster("Data & Storage", graph_attr={"bgcolor": "#E0F2F1", "style": "rounded"}):
                    s3_bucket = S3("S3 Bucket\nDocuments & Reports")
                    cache_layer = Python("In-Memory Cache\nPandas DataFrames")
        
        # Container Registry & CI/CD
        with Cluster("Container Services", graph_attr={"bgcolor": "#FFF3E0", "style": "rounded"}):
            ecr_repo = ECR("ECR Repository\npeer-bank-analytics")
            codebuild = Codebuild("CodeBuild\nContainer Build")
        
        # Management & Security
        with Cluster("Management & Security", graph_attr={"bgcolor": "#FFF8DC", "style": "rounded"}):
            cloudwatch = Cloudwatch("CloudWatch\nLogs & Metrics")
            iam = IAM("IAM Roles\n& Policies")
            secrets = SecretsManager("Secrets Manager\nAPI Keys")
            ssm = SystemsManager("Systems Manager\nParameter Store")
    
    # Step 1: User Access
    users >> Edge(label="1. HTTPS Request", color="#FF9900", style="bold") >> internet
    admin_users >> Edge(label="Admin Access", color="#FF6B6B", style="dashed") >> internet
    
    # Step 2: Load Balancing
    internet >> Edge(label="2. Route Traffic", color="#FF9900") >> igw >> alb
    
    # Step 3: Container Orchestration
    alb >> Edge(label="3. Forward Request", color="#4CAF50") >> ecs_cluster
    ecs_cluster >> fargate_service >> container_app
    
    # Step 4: External Data Integration
    container_app >> Edge(label="4. Fetch Banking Data", color="#2196F3") >> fdic_api
    container_app >> Edge(label="5. Retrieve Reports", color="#2196F3") >> sec_api
    
    # Step 6: AI/ML Processing
    container_app >> Edge(label="6. AI Analysis", color="#9C27B0") >> bedrock
    container_app >> Edge(label="7. Vector Search", color="#9C27B0") >> vector_db
    
    # Step 8: Data Management
    container_app >> Edge(label="8. Document Storage", color="#FF5722") >> s3_bucket
    container_app >> Edge(label="9. Performance Cache", color="#FF5722") >> cache_layer
    
    # CI/CD Pipeline
    codebuild >> Edge(label="Build & Push", color="#FF9800") >> ecr_repo
    ecr_repo >> Edge(label="Deploy Image", color="#FF9800") >> fargate_service
    
    # Infrastructure Services
    fargate_service >> Edge(label="Application Logs", color="#607D8B") >> cloudwatch
    container_app >> Edge(label="Secure Credentials", color="#795548") >> secrets
    fargate_service >> Edge(label="IAM Permissions", color="#795548") >> iam
    container_app >> Edge(label="Configuration", color="#607D8B") >> ssm