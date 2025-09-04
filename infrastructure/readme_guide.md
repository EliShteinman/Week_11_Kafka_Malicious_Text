# Kafka Malicious Text - Kubernetes Deployment

מעבר מ-Docker Compose ל-Kubernetes עם כל השירותים שלך.

## 📁 קבצים

### Infrastructure (תשתית)
- `01-namespace.yaml` - Namespace לכל הפרוייקט
- `02-kafka-config.yaml` - הגדרות Kafka
- `03-kafka-statefulset.yaml` - Kafka StatefulSet
- `04-kafka-services.yaml` - Services של Kafka
- `05-mongodb-statefulset.yaml` - MongoDB StatefulSet
- `06-mongodb-services.yaml` - Services של MongoDB

### UIs (ממשקי משתמש)
- `07-kafka-ui.yaml` - Kafka UI
- `08-mongo-express.yaml` - Mongo Express

### Application Configuration
- `09-app-config.yaml` - ConfigMaps ו-Secrets

### Microservices (המיקרו-סרביסים שלך)
- `10-data-retrieval.yaml` - Data Retrieval Service
- `11-retriever.yaml` - Retriever Service
- `12-preprocessor.yaml` - Preprocessor Service  
- `13-enricher.yaml` - Enricher Service
- `14-persister.yaml` - Persister Service

### Networking & Security
- `15-ingress.yaml` - Ingress לגישה חיצונית
- `16-network-policies.yaml` - Network Policies לאבטחה

### Scripts (סקריפטים)
- `build-and-push.sh` - בנייה והעלאה של תמונות Docker
- `update-images.sh` - עדכון הפניות לתמונות ב-YAML
- `deployment-script.sh` - סקריפט פריסה אוטומטי

## 🚀 איך להריץ

### שלב 1: הכנת תמונות Docker
```bash
# 1. ערוך את build-and-push.sh - עדכן את REGISTRY
vim build-and-push.sh

# 2. בנה ודחוף תמונות
chmod +x build-and-push.sh
./build-and-push.sh
```

### שלב 2: עדכון YAML files
```bash
# ערוך את update-images.sh - עדכן את REGISTRY
vim update-images.sh

# הרץ את הסקריפט
chmod +x update-images.sh
./update-images.sh
```

### שלב 3: פריסה
```bash
# הרץ את סקריפט הפריסה
chmod +x deployment-script.sh
./deployment-script.sh
```

## 🔧 פקודות שימושיות

### בדיקת סטטוס
```bash
# כל הresources
kubectl get all -n kafka-malicious-text

# רק pods
kubectl get pods -n kafka-malicious-text

# עם watch
kubectl get pods -n kafka-malicious-text -w
```

### צפייה ב-logs
```bash
# Kafka
kubectl logs -f kafka-0 -n kafka-malicious-text

# Microservice
kubectl logs -f deployment/retriever -n kafka-malicious-text

# כל ה-pods של service מסוים
kubectl logs -l app=preprocessor -n kafka-malicious-text --tail=50
```

### גישה ל-UIs
```bash
# Kafka UI (http://localhost:9080)
kubectl port-forward service/kafka-ui 9080:8080 -n kafka-malicious-text

# Mongo Express (http://localhost:8081) 
kubectl port-forward service/mongo-express 8081:8081 -n kafka-malicious-text

# Data Retrieval API (http://localhost:8082)
kubectl port-forward service/data-retrieval 8082:8082 -n kafka-malicious-text
```

### Scaling
```bash
# הגדלת מספר replicas
kubectl scale deployment preprocessor --replicas=5 -n kafka-malicious-text
kubectl scale deployment enricher --replicas=3 -n kafka-malicious-text

# בדיקת מספר replicas נוכחי
kubectl get deployments -n kafka-malicious-text
```

### Debug
```bash
# פרטי pod
kubectl describe pod kafka-0 -n kafka-malicious-text

# כניסה לpod
kubectl exec -it kafka-0 -n kafka-malicious-text -- bash

# רשימת topics ב-Kafka
kubectl exec -it kafka-0 -n kafka-malicious-text -- \
  kafka-topics --bootstrap-server localhost:29092 --list
```

## 🔄 הבדלים מ-Docker Compose

| Docker Compose | Kubernetes | הסבר |
|----------------|------------|------|
| `networks` | `Services` + `NetworkPolicies` | קישוריות ואבטחה |
| `volumes` | `PersistentVolumeClaims` | אחסון מתמיד |
| `depends_on` | `readinessProbe` | סדר הפעלה |
| `environment` | `ConfigMaps` + `Secrets` | משתני סביבה |
| `restart: unless-stopped` | `restartPolicy: Always` | אוטומטי ב-K8s |
| Manual scaling | `kubectl scale` | קל וגמיש |

## 📊 מבנה הArchitecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Kafka UI      │    │  Mongo Express   │    │ Data Retrieval  │
│   (Port 9080)   │    │   (Port 8081)    │    │   (Port 8082)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                        │
│                                                                 │
│  ┌───────────────┐              ┌─────────────────┐            │
│  │     Kafka     │◄────────────►│    MongoDB      │            │
│  │ (StatefulSet) │              │ (StatefulSet)   │            │
│  └───────────────┘              └─────────────────┘            │
│         ▲                                ▲                     │
│         │                                │                     │
│  ┌──────┴────────┐  ┌────────────────────┴──────────────┐     │
│  │  Retriever    │  │           Persister               │     │
│  └───────────────┘  └───────────────────────────────────┘     │
│         │                                ▲                     │
│         ▼                                │                     │
│  ┌──────────────────┐          ┌────────────────┐              │
│  │   Preprocessor   │─────────►│   Enricher     │              │
│  │   (2 replicas)   │          │  (2 replicas)  │              │
│  └──────────────────┘          └────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## 🛡️ אבטחה

- **NetworkPolicies**: בקרת תעבורת רשת
- **Secrets**: אחסון מאובטח של סיסמאות
- **RBAC**: בקרת הרשאות (לא מומש כאן)
- **Pod Security**: הגבלות אבטחה על containers

## 📈 מעקב וניטור

עבור production מומלץ להוסיף:
- **Prometheus + Grafana** לניטור
- **ELK Stack** לlogים
- **Jaeger** לtracing
- **ArgoCD** ל-GitOps

## ❓ פתרון בעיות נפוצות

### Pod לא עולה
```bash
kubectl describe pod POD_NAME -n kafka-malicious-text
kubectl logs POD_NAME -n kafka-malicious-text
```

### בעיות אחסון
```bash
kubectl get pvc -n kafka-malicious-text
kubectl describe pvc DATA_PVC_NAME -n kafka-malicious-text
```

### בעיות רשת
```bash
# בדיקת services
kubectl get services -n kafka-malicious-text

# בדיקת endpoints
kubectl get endpoints -n kafka-malicious-text
```

### תמונות Docker לא נמצאות
וודא ש:
1. התמונות נדחפו ל-registry
2. הPull secrets מוגדרים אם צריך
3. שמות התמונות נכונים ב-YAML files