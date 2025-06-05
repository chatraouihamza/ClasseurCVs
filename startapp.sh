#!/bin/bash
echo ">>> S'assurer que l'image Docker existe localement..."
docker images | grep classeur-cv-app | grep v1 > /dev/null
if [ $? -ne 0 ]; then
  echo ">>> Image classeur-cv-app:v1 non trouvée. Construction..."
  docker build -t classeur-cv-app:v1 .
  if [ $? -ne 0 ]; then
    echo "ERREUR: Échec de la construction de l'image Docker."
    exit 1
  fi
else
  echo ">>> Image classeur-cv-app:v1 trouvée."
fi

echo ""
echo ">>> Création du cluster Kind 'mon-classeur-k8s-cluster'..."
kind create cluster --name mon-classeur-k8s-cluster
if [ $? -ne 0 ]; then
  echo "ERREUR: Échec de la création du cluster Kind."
  # Tenter de supprimer un cluster existant s'il cause problème et réessayer
  echo ">>> Tentative de suppression d'un cluster existant du même nom et nouvelle tentative..."
  kind delete cluster --name mon-classeur-k8s-cluster
  kind create cluster --name mon-classeur-k8s-cluster
  if [ $? -ne 0 ]; then
    echo "ERREUR: Échec de la création du cluster Kind même après suppression."
    exit 1
  fi
fi

echo ""
echo ">>> Chargement de l'image Docker 'classeur-cv-app:v1' dans le cluster Kind..."
kind load docker-image classeur-cv-app:v1 --name mon-classeur-k8s-cluster
if [ $? -ne 0 ]; then
  echo "ERREUR: Échec du chargement de l'image dans Kind."
  exit 1
fi

echo ""
echo ">>> Application des manifestes Kubernetes..."
kubectl apply -f classeur-cv-k8s.yaml
if [ $? -ne 0 ]; then
  echo "ERREUR: Échec de l'application des manifestes Kubernetes."
  exit 1
fi

echo ""
echo ">>> Attente que le Pod devienne 'Running' (max 2 minutes)..."
kubectl wait --for=condition=Ready pod -l app=classeur-cv --timeout=120s
if [ $? -ne 0 ]; then
  echo "ATTENTION: Le Pod n'est pas devenu 'Ready' dans le temps imparti. Vérifiez avec 'kubectl get pods' et 'kubectl logs <pod-name>'."
else
  echo ">>> Pod prêt !"
fi

echo ""
echo ">>> Lancement de kubectl port-forward pour service/classeur-cv-service sur localhost:8080..."
echo ">>> Accédez à votre application sur http://localhost:8080"
echo ">>> Appuyez sur Ctrl+C dans CE terminal pour arrêter le port-forward et le script."
kubectl port-forward service/classeur-cv-service 8080:8000





# 
#  chmod +x startapp.sh puis ./startapp.sh