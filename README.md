# Zadanie 2 - Łańcuch CI w Github Actions - Programowanie Aplikacji w Chmurze Obliczeniowej

Polecenie:

Opracować łańcuch (pipeline) w usłudzie GitHub Actions, który zbuduje obraz kontenera na podstawie Dockerfile-a oraz kodów źródłowych aplikacji opracowanej jako rozwiązanie zadania nr 1 a następnie prześle go do publicznego repozytorium autora na Github (ghcr.io). Proces budowania obrazu opisany w łańcuchu GHAction powinien dodatkowo spełniać następujące warunki: 

 1. Obraz wspierać ma dwie architektury: linux/arm64 oraz
    linux/amd64.

 2. Wykorzystywane mają być (wysyłanie i pobieranie) dane cache   
    (eksporter: registry oraz backend-u registry w trybie max). Te dane 
    cache powinny być przechowywane w dedykowanym, publicznym   
    repozytorium autora na DockerHub.

 3. Ma być wykonany test CVE    obrazu, który zapewni, że obraz zostanie
    przesłany do publicznego  repozytorium obrazów na GitHub tylko
    wtedy gdy nie będzie zawierał  zagrożeń sklasyfikowanych jako
    krytyczne lub wysokie.

UWAGA: Test CVE może zostać wykonany tak w oparciu o Docker Scout lub skaner Trivy. Proszę się zastanowić, które z rozwiązań będzie najlepsze/najprostsze dla realizacji tego testu.

## Finalny workflow
Test na CVE został wykonany przy użyciu Docker Scout'a, zmienne środowiskowe zostały ustawione w repo na githubie.

	name: Z2 - Build and Push Docker Image

	on:
	  push:
	    branches: [ main ]
	    tags:
	      - 'v*'
	  workflow_dispatch:

	jobs:
	  build-and-push:
	  name: Build, Scan and Push Image
      runs-on: ubuntu-latest

    permissions:
      contents: read
      packages: write
      id-token: write

    env:
      IMAGE_NAME: ghcr.io/nightxpl01/zadanko1-cld
      CACHE_IMAGE: ${{ format('docker.io/{0}/zadanko1-cache:latest', secrets.DOCKERHUB_USERNAME) }}

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Install Docker Scout
      run: |
        curl -sSfL https://raw.githubusercontent.com/docker/scout-cli/main/install.sh | sh -s -- -b /usr/local/bin

    - name: Log in to GHCR
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Log in to DH
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}

    - name: Build temp image (for Scout)
      uses: docker/build-push-action@v5
      with:
        context: .
        push: false
        load: true
        platforms: linux/amd64 
        tags: ${{ env.IMAGE_NAME }}:temp
        cache-from: type=registry,ref=${{ env.CACHE_IMAGE }}
        cache-to: type=registry,ref=${{ env.CACHE_IMAGE }},mode=max

    - name: Docker Scout Scan
      run: |
        docker-scout cves ${{ env.IMAGE_NAME }}:temp --format sarif --output cve-results.sarif
        SEVERITY_COUNT=$(docker-scout cves ${{ env.IMAGE_NAME }}:temp --format json | grep -E '"severity":"(high|critical)"' | wc -l)
        echo "Found $SEVERITY_COUNT high/critical vulnerabilities"
        test "$SEVERITY_COUNT" -eq 0

    - name: Push to GHCR
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
         ${{ env.IMAGE_NAME }}:latest
         ${{ env.IMAGE_NAME }}:${{ github.sha }}
         ${{ env.IMAGE_NAME }}:${{ github.ref_name }}
        platforms: linux/amd64,linux/arm64
        cache-from: type=registry,ref=${{ env.CACHE_IMAGE }}
        cache-to: type=registry,ref=${{ env.CACHE_IMAGE }},mode=max


		
## Krok 1 - wstępne ustawienia łańcucha

    name: Z2 - Build and Push Docker Image  //nazwa
    
    //trigger uruchomienia łańcucha: przy pushu do main, przy pushu z 'vXXX' i ręcznym (workflow_dispatch)
    on:
      push:
        branches: [ main ]
        tags:
          - 'v*'
      workflow_dispatch:
    //zadania
    
    jobs:
      build-and-push:
        name: Build, Scan and Push Image
        runs-on: ubuntu-latest
        
    //uprawnienia
        permissions:
          contents: read
          packages: write
          id-token: write
          
    //zmienne środowiskowe
        env:
          IMAGE_NAME: ghcr.io/nightxpl01/zadanko1-cld
          CACHE_IMAGE: ${{ format('docker.io/{0}/zadanko1-cache:latest', secrets.DOCKERHUB_USERNAME) }}


## Krok 2 - Poszczególne kroki łańcucha

	steps:
	//checkout - sprawdzenie czy jest dostęp do ustawionego repo na zasadach określonych w konfiguracji modułu
    - name: Checkout repository
      uses: actions/checkout@v4
      
	//przygotowanie Buildx'a
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
      
	//Instalacja Docker Scouta w wersji CLI
    - name: Install Docker Scout
      run: |
        curl -sSfL https://raw.githubusercontent.com/docker/scout-cli/main/install.sh | sh -s -- -b /usr/local/bin

	//Logowanie do Github Container Registry (GHCR)
    - name: Log in to GHCR
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
        
	//Logowanie to DockerHub'a przez token
    - name: Log in to DH
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}

	//Zbudowanie tymczasowego obrazu do skanu dla Scouta na platformie AMD64
    - name: Build temp image (for Scout)
      uses: docker/build-push-action@v5
      with:
        context: .
        push: false
        load: true
        platforms: linux/amd64 
        tags: ${{ env.IMAGE_NAME }}:temp
        cache-from: type=registry,ref=${{ env.CACHE_IMAGE }}
        cache-to: type=registry,ref=${{ env.CACHE_IMAGE }},mode=max

	//Skan Scout'a z sformatowanym wydrukiem wyników (tylko high/critical CVE są liczone)
    - name: Docker Scout Scan
      run: |
        docker-scout cves ${{ env.IMAGE_NAME }}:temp --format sarif --output cve-results.sarif
        SEVERITY_COUNT=$(docker-scout cves ${{ env.IMAGE_NAME }}:temp --format json | grep -E '"severity":"(high|critical)"' | wc -l)
        echo "Found $SEVERITY_COUNT high/critical vulnerabilities"
        test "$SEVERITY_COUNT" -eq 0

	//Push do rejestru jeżeli test nie wykazał więcej niż '0' błędów, tryb max i na dwie platformy ARM64 i AMD64
    - name: Push to GHCR
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
         ${{ env.IMAGE_NAME }}:latest
         ${{ env.IMAGE_NAME }}:${{ github.sha }}
         ${{ env.IMAGE_NAME }}:${{ github.ref_name }}
        platforms: linux/amd64,linux/arm64
        cache-from: type=registry,ref=${{ env.CACHE_IMAGE }}
        cache-to: type=registry,ref=${{ env.CACHE_IMAGE }},mode=max

## Krok 3 - Tagi w łańcuchu

    ${{ env.IMAGE_NAME }}:temp // tag temp, używany do oznaczenia tymczasowego obrazu dla Scout'a
    
    ${{ env.IMAGE_NAME }}:latest // tag latest, używany do ostatecznego kroku, push'u do GHCR gdy nie ma błędów w kroku skanu
    
    CACHE_IMAGE: ${{ format('docker.io/{0}/zadanko1-cache:latest', secrets.DOCKERHUB_USERNAME) }} 
    // tag cache, oznacza cache na dockerhubie dla użytkownika podanego w zmiennych środowiskowych ustawionych na githubie w repo
    
    ${{ env.IMAGE_NAME }}:${{ github.sha }} // dodaje unikalny tag o wartości sha do obrazu

	${{ env.IMAGE_NAME }}:${{ github.ref_name }} // tag o wartości branch'a który wywołał workflow (np. main)

## Źródła
https://docs.docker.com/build/ci/github-actions/manage-tags-labels/

https://github.com/marketplace/actions/docker-build-push-action

https://github.com/docker/metadata-action?tab=readme-ov-file#tags-input

https://docs.github.com/en/actions/use-cases-and-examples/publishing-packages/publishing-docker-images

https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#onpushbranchestagsbranches-ignoretags-ignore

https://github.com/marketplace/actions/docker-login

https://github.com/marketplace/actions/docker-scout


## Autor rozwiązania

Michał Grzegorz Małysz 
Grupa 6.8

## Autor zadania

Dr inż. Sławomir Przyłucki 

s.przylucki@pollub.pl
