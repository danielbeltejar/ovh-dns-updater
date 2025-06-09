# OVH DNS Updater  

A Python script to automatically update OVH DNS records with your current public IP address (IPv4 and/or IPv6). Designed for use in Kubernetes environments or standalone deployments.  

---

## 📌 Overview  

This project periodically checks your public IP address and updates specified OVH DNS records to ensure they always point to your current IP. It supports both IPv4 and IPv6, and integrates with Kubernetes via a CronJob for automated execution.  

---

## ✅ Features  

- **Automatic IP Detection**: Uses multiple services to fetch your current public IP address.  
- **OVH API Integration**: Updates A and AAAA records via the OVH API.  
- **Configurable TTL**: Set custom TTL values for DNS records.  
- **Kubernetes Deployment**: Includes a CronJob and ConfigMap for Kubernetes environments.  
- **IPv4/IPv6 Support**: Handles both IP versions seamlessly.  

---