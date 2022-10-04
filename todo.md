# Funderingar

- Bestäm vilka regioner av USA vi kan utesluta. Bestäm genom att analysera akamai trace och ta de minst utiliserade regionerna
- Få ut request rate från varje region genom akamai dataset:et. (se request.csv)
- Gör så vi kan köra akamai simulation



# Steg
- Preprocessing
    1. Gör en fil av carbon intensity data (azure -> 1 csv)
    2. Latency data (bort med pickle! -> 1 csv)
    3. Integrera Akamai data (kombinera alla små filer till en enda fil)
-


# Misc
- `carbon_map_na` plotta data geografiskt
- `latency_vs_carbon_plot` -> `casper`

# Resultat

1. Gör analys av akamai ihop med carbon intensity och latency
2. Simulera med delar av akamai (allt utom vart alla requests har placerats) vilket förhoppningsvis ska ge liknande reslutat som (1)