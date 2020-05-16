# #!/usr/bin/env Rscript
# args = commandArgs(trailingOnly=TRUE)

# if (length(args)<1) {
#   stop("Please inform input and output file 
        
#         RScript [program.R] [input_file] [output_file]", call.=FALSE)
# } 

# PARTY_MIN_TRESHOLD=1

# ## program...
# input_file = args[1]
# # output_file = args[2]

# voteboard <- read.csv("./results/probabilities/probabilities_38500_3500.csv", header = TRUE, stringsAsFactors=F)
voteboard <- read.csv(input_file, header = TRUE, stringsAsFactors=F)


voteboard["emPoder"] <- ifelse(voteboard$is_governo == "True" | voteboard$proposedBy == "Governo", TRUE, FALSE)

voteboard["BID"] <- voteboard$BID..numberInt

rownames(voteboard) <- 1:nrow(voteboard)

voteboard["proposedBy_aux"] <- voteboard$proposedBy

PARTY_MIN_TRESHOLD = 50
# parties_aux <- names(which(table(voteboard$proposedBy_aux)<50))

low_frequency_parties <- names(which(table(voteboard$proposedBy_aux)<PARTY_MIN_TRESHOLD))

if(length(low_frequency_parties) > 0) {
  for(i in 1:length(low_frequency_parties)) {
    voteboard[voteboard[, "proposedBy_aux"] == low_frequency_parties[i],]$proposedBy_aux <- "Outro"
  }
}

# Get list of parties  
parties <- unique(as.character(voteboard$proposedBy_aux))
print(parties)
# Init parties dataframe
party_probabilities_df <- data.frame(Party=parties, Probab=0)

# Calculate inverse propability for each party
for(i in 1:nrow(party_probabilities_df)) {
  party_probabilities_df[i,]$Probab <- 1 - (nrow(voteboard[voteboard[, "proposedBy_aux"] == as.character(party_probabilities_df[i,]$Party),])/nrow(voteboard))
}

library("DMwR")
party_probabilities_df$Probab <- DMwR::SoftMax(party_probabilities_df$Probab,lambda = 4)

voteboard["Probab"] <- party_probabilities_df[match(voteboard$proposedBy_aux,party_probabilities_df$Party),]$Probab

sample_hits <- c()

prop_hits <- c()

round_votes <- data.frame(PSD=numeric(0),PS=numeric(0), CDS_PP=numeric(0),
                          PCP=numeric(0), BE=numeric(0), PEV=numeric(0), PAN=numeric(0))

for(i in 1:1000) {

  ids <- c(sample(rownames(voteboard[voteboard$emPoder==TRUE,]),5,prob = voteboard[voteboard$emPoder==TRUE,]$Probab),
           sample(rownames(voteboard[voteboard$emPoder==FALSE,]),5,prob = voteboard[voteboard$emPoder==FALSE,]$Probab))

  vote_sample <- voteboard[as.numeric(ids),]
  round_votes <- rbind(round_votes,as.data.frame(t(colSums(vote_sample[,c("PSD","PS","CDS_PP","PS","PCP","BE","PEV","PAN")],na.rm=TRUE))))

  sample_hits <- c(sample_hits,as.character(voteboard[ids,]$proposedBy))
  
  prop_hits <- c(prop_hits,voteboard[ids,]$BID)
  
}

summary(round_votes)