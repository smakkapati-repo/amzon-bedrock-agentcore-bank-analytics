from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, Fargate, ECR
from diagrams.aws.network import InternetGateway, ElasticLoadBalancing, VPC
from diagrams.aws.storage import S3
from diagrams.aws.devtools import Codebuild
from diagrams.aws.ml import Bedrock
from diagrams.aws.management import Cloudwatch, SystemsManager
from diagrams.aws.security import IAM, SecretsManager
from diagrams.aws.general import User, Users, Client
from diagrams.aws.database import Dynamodb
from diagrams.onprem.client import Users as ExternalUsers
from diagrams.onprem.compute import Server
from diagrams.onprem.inmemory import Redis
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
    "Banking Peer Analytics Platform - AWS Architecture",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
    filename="banking_peer_analytics_architecture"
):
    
    with Cluster("External Data Sources", graph_attr={"bgcolor": "white", "style": "rounded", "rankdir": "LR"}):
        fdic_api = Server("FDIC APIs\nReal-time Banking Data")
        sec_api = Server("SEC EDGAR APIs\nFinancial Reports")
        
        # Force horizontal alignment
        fdic_api - sec_api
    
    with Cluster("Users", graph_attr={"bgcolor": "white", "style": "rounded"}):
        users = ExternalUsers("Banking Analysts\n& Executives")
        admin_users = User("System Administrators")
    

    
    with Cluster("AWS Cloud Services", graph_attr={"bgcolor": "white", "style": "rounded", "color": "#232F3E"}):
        
        # VPC
        with Cluster("VPC - us-east-1", graph_attr={"bgcolor": "white", "style": "rounded"}):
            
            # Internet Gateway
            igw = InternetGateway("Internet Gateway")
            
            # Public Subnet
            with Cluster("Public Subnet", graph_attr={"bgcolor": "white", "style": "rounded"}):
                alb = ElasticLoadBalancing("Application\nLoad Balancer")
                
                # ECS Fargate Services
                with Cluster("ECS Fargate Cluster", graph_attr={"bgcolor": "white", "style": "rounded"}):
                    ecs_cluster = ECS("ECS Cluster\npeer-bank-analytics")
                    fargate_service = Fargate("Fargate Service\nReact + Flask App")
                
                # AI/ML Services
                with Cluster("AI/ML Services", graph_attr={"bgcolor": "white", "style": "rounded"}):
                    bedrock = Bedrock("Amazon Bedrock\nClaude 3.5 Sonnet")
                    vector_db = Redis("Vector Store\nFAISS Embeddings")
                
                # Data Services
                with Cluster("Data & Storage", graph_attr={"bgcolor": "white", "style": "rounded"}):
                    s3_bucket = S3("S3 Bucket\nDocuments & Reports")
        
        # Container Registry
        with Cluster("Container Services", graph_attr={"bgcolor": "white", "style": "rounded"}):
            ecr_repo = ECR("ECR Repository\npeer-bank-analytics")
        
        # Management & Security
        with Cluster("Management & Security", graph_attr={"bgcolor": "white", "style": "rounded", "rankdir": "LR", "ranksep": "0.1"}):
            with Cluster("", graph_attr={"style": "invis", "rank": "same"}):
                cloudwatch = Cloudwatch("CloudWatch\nLogs & Metrics")
                iam = IAM("IAM Roles\n& Policies")
                secrets = SecretsManager("Secrets Manager\nAPI Keys")
                
                # Force perfect horizontal alignment
                cloudwatch - iam - secrets
    
    # Step 1: User Access
    users >> Edge(label="1. HTTP Request", color="#FF9900", style="bold") >> igw >> alb
    admin_users >> Edge(label="Admin Access", color="#FF6B6B", style="dashed") >> igw >> alb
    
    # Step 2: Container Orchestration
    alb >> Edge(label="2. Forward Request", color="#4CAF50") >> ecs_cluster
    ecs_cluster >> fargate_service
    
    # Step 3: External Data Integration
    fargate_service >> Edge(label="3. Fetch Banking Data", color="#2196F3") >> fdic_api
    fargate_service >> Edge(label="4. Retrieve Reports", color="#2196F3", labeldistance="0.1", labelangle="0") >> sec_api
    
    # Step 5: AI/ML Processing
    fargate_service >> Edge(label="5. AI Analysis", color="#9C27B0") >> bedrock
    fargate_service >> Edge(label="6. Vector Search", color="#9C27B0") >> vector_db
    
    # Step 7: Data Management
    fargate_service >> Edge(label="7. Document Storage", color="#FF5722") >> s3_bucket
    
    # Container Deployment
    ecr_repo >> Edge(label="Deploy Image", color="#FF9800") >> fargate_service
    
    # Infrastructure Services - single connection to cluster
    fargate_service >> Edge(label="Logs, Credentials & Permissions", color="#607D8B") >> cloudwatch