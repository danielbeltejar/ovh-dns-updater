pipeline {
    agent {
        kubernetes {
            inheritFrom 'kaniko'
            defaultContainer 'kaniko'
            yaml """
            apiVersion: v1
            kind: Pod
            metadata:
            spec:
              containers:
              - name: kaniko
                image: 'gcr.io/kaniko-project/executor:debug'
                command:
                - sleep
                args:
                - infinity
                volumeMounts:
                - name: docker-config
                  mountPath: /kaniko/.docker
                - name: ca-certificate
                  mountPath: /kaniko/.docker/certs/
              - name: helm
                image: 'mirror.gcr.io/alpine/helm'
                command:
                - sleep
                args:
                - infinity
              - name: git
                image: 'mirror.gcr.io/alpine/git'
                command:
                - sleep
                args:
                - infinity
              restartPolicy: Never
              volumes:
              - name: docker-config
                configMap:
                  name: docker-auth-config
              - name: ca-certificate
                hostPath:
                  path: /nfs/lab-jenkins/certs/
            """
        }
    }

    environment {
        GIT_CREDENTIALS = credentials('GITHUB_AUTH_TOKEN')
        DISCORD_CREDENTIALS = credentials('DISCORD_CREDENTIALS')
        HARBOR_CREDENTIALS = credentials('HARBOR_CREDENTIALS')
        
        GIT_URL = "https://${GIT_CREDENTIALS}@github.com/${params.GIT_URL.split('github.com/')[1]}"
        
        REGISTRY_URL = "harbor.server.local"
        HELM_RELEASE_NAME = "${JOB_NAME.replaceAll("[^a-zA-Z0-9]", "-").toLowerCase()}"
        HELM_CHART_DIR = "k8s/"
        IMAGE_REPO = "${GIT_URL.tokenize("/")[-1].replaceAll(".git", "").toLowerCase()}"
        IMAGE_VERSION_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout Source Code') {
            steps {
                container('kaniko') {
                    checkout([$class: 'GitSCM',
                              branches: [[name: 'main']],
                              userRemoteConfigs: [[url: "${GIT_URL}"]]
                    ])
                }
            }
        }
        stage('Configure Environment') {
            steps {
                container('kaniko') {
                    script {
                        sh '''
                        echo "192.168.1.105 ${REGISTRY_URL}" | tee -a /etc/hosts
                        '''
                    }
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                container('kaniko') {
                    script {
                        def dockerfileContent = readFile("Dockerfile")
                        def fromCount = dockerfileContent.split('\n').findAll { it.trim().startsWith('FROM') }.size()
                        def ignorePathOption = fromCount > 1 ? '--ignore-path /' : ''
                        
                        sh """
                        /kaniko/executor \
                        --context=`pwd` \
                        --dockerfile=`pwd`/Dockerfile \
                        --destination=${REGISTRY_URL}/danielbeltejar/${IMAGE_REPO}:${IMAGE_VERSION_TAG} \
                        --destination=${REGISTRY_URL}/danielbeltejar/${IMAGE_REPO}:latest \
                        --cache=false \
                        --cache-dir=/cache \
                        --snapshot-mode=redo \
                        --registry-certificate "${REGISTRY_URL}=/kaniko/.docker/certs/ca.crt" \
                        ${ignorePathOption}
                        """
                    }
                }
            }
        }
    }
}
