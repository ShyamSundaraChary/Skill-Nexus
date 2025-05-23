USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.91",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.97",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
]


SKILLS_LIST = [
    "c", "c++", "java", "python", "javascript", "typescript", "c#", "php", "go", "rust", "swift", "kotlin", "ruby",
    "scala", "perl", "r", "matlab", "groovy", "dart", "haskell", "elixir", "clojure", "f#", "lua", "erlang",
    "html", "html5", "css", "css3", "react", "react.js", "next.js", "angular", "vue.js", "svelte", "node.js",
    "express.js", "django", "flask", "spring boot", "laravel", "asp.net", "fast api", "ruby on rails", "jquery",
    "bootstrap", "tailwind css", "material ui", "chakra ui", "styled components", "sass", "less", "webpack",
    "babel", "gulp", "grunt", "npm", "yarn", "redux", "mobx", "graphql", "apollo", "socket.io", "websocket",
    "sql", "mysql", "postgresql", "mongodb", "firebase", "sqlite", "redis", "cassandra", "oracle db", "dynamodb",
    "neo4j", "couchdb", "elasticsearch", "kibana", "hbase", "bigtable", "cosmos db", "mariadb", "db2",
    "machine learning", "deep learning", "data analysis", "data visualization", "tensorflow", "pytorch", "pandas",
    "numpy", "scikit-learn", "opencv", "natural language processing (nlp)", "keras", "xgboost", "matplotlib",
    "seaborn", "plotly", "d3.js", "tableau", "power bi", "spark", "hadoop", "hive", "pig", "kafka", "flink",
    "computer vision", "reinforcement learning", "statistics", "probability", "linear algebra", "time series analysis",
    "recommendation systems", "nlp", "sentiment analysis", "text mining", "data mining", "predictive modeling",
    "aws", "google cloud", "microsoft azure", "docker", "kubernetes", "jenkins", "terraform", "git", "ci/cd",
    "ci/cd pipelines", "ansible", "puppet", "chef", "cloudformation", "serverless", "lambda", "ec2", "s3",
    "gcp", "gcp bigquery", "azure", "azure devops", "github actions", "gitlab ci", "circleci", "travis ci",
    "prometheus", "grafana", "elk stack", "splunk", "new relic", "datadog", "cloudwatch", "azure monitor",
    "ethical hacking", "penetration testing", "network security", "cryptography", "firewalls", "wireshark",
    "metasploit", "burp suite", "nmap", "owasp", "secure coding", "security compliance", "vulnerability assessment",
    "incident response", "security monitoring", "siem", "soc", "pci dss", "gdpr", "hipaa", "iso 27001",
    "linux", "shell scripting", "windows server", "kernel development", "bash", "powershell", "unix", "ubuntu",
    "centos", "redhat", "debian", "macos", "windows", "vmware", "virtualization", "hyper-v", "active directory",
    "dns", "dhcp", "ldap", "samba", "nfs", "iscsi", "raid", "backup solutions", "disaster recovery",
    "git & github", "agile", "scrum", "design patterns", "software testing", "oop", "system design", "microservices",
    "rest", "rest apis", "restful apis", "graphql", "websockets", "soap", "grpc", "api gateway", "swagger",
    "postman", "jira", "confluence", "trello", "slack", "microsoft teams", "zoom", "code review", "pair programming",
    "tdd", "bdd", "ddd", "clean code", "solid principles", "design patterns", "architecture patterns", "Data Structures",
    "Algorithms", "Big O Notation", "Recursion", "Dynamic Programming", "Greedy Algorithms", "Graph Algorithms",
    "unit testing", "integration testing", "selenium", "pytest", "junit", "test automation", "mocking",
    "jest", "mocha", "chai", "cypress", "playwright", "testng", "qa automation", "manual testing", "performance testing",
    "load testing", "security testing", "api testing", "mobile testing", "cross-browser testing",
    "big data", "hadoop", "spark", "kafka", "flink", "hive", "pig", "data warehousing", "database fundamentals",
    "data modeling", "etl", "data integration", "business intelligence", "data governance", "data quality",
    "data lakes", "data mesh", "data fabric", "data pipelines", "airflow", "luigi", "prefect",
    "blockchain", "solidity", "ethereum", "smart contracts", "web3", "hyperledger", "truffle", "ganache",
    "metamask", "ipfs", "defi", "nft", "cryptocurrency", "consensus algorithms", "distributed ledger",
    "game development", "unity", "unreal engine", "opengl", "directx", "cocos2d", "phaser", "godot",
    "game design", "3d modeling", "animation", "physics engines", "game ai", "multiplayer networking",
    "android development", "ios development", "flutter", "react native", "xamarin", "kotlin", "swift",
    "objective-c", "android studio", "xcode", "mobile ui/ux", "mobile security", "push notifications",
    "mobile analytics", "app store optimization", "cross-platform development",
    "embedded systems", "iot", "arduino", "raspberry pi", "rtos", "microcontrollers", "sensors",
    "wireless protocols", "mqtt", "coap", "zigbee", "bluetooth", "wifi", "lora", "nb-iot",
    "edge computing", "firmware development", "device drivers", "hardware programming",
    "project management", "team leadership", "communication", "problem solving", "critical thinking",
    "time management", "agile methodologies", "scrum master", "product owner", "stakeholder management",
    "risk management", "budget management", "resource allocation", "conflict resolution",
    "technical writing", "documentation", "api documentation", "user guides", "technical specifications",
    "markdown", "confluence", "readme", "wiki", "knowledge base", "documentation tools",
    "git", "github", "gitlab", "bitbucket", "svn", "mercurial", "version control", "branching strategies",
    "code review", "pull requests", "merge conflicts", "continuous integration", "continuous deployment"
]
