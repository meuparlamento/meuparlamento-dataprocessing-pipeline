#!/usr/bin/env Rscript
args = commandArgs(trailingOnly=TRUE)

# test if there is at least one argument: if not, return an error
if (length(args)<2) {
  stop("Please inform input and output file 
        
        RScript [program.R] [input_file] [output_file]", call.=FALSE)
} 

PARTY_MIN_TRESHOLD=1

## program...
input_file = args[1]
output_file = args[2]

# Load data
voteboard_df <- read.csv("results/probabilities/aggregated_voting_data_38500_3500.csv", header = TRUE, stringsAsFactors=FALSE)
# voteboard_df <- read.csv(input_file, header = TRUE, stringsAsFactors=F)

# Create an auxiliary attribute for encapsulating entries in proposedBy that have small numbers
voteboard_df["proposedBy_aux"] <- voteboard_df$proposedBy

# Create a category "Outro" for entries with less than N PARTY_MIN_TRESHOLD
low_frequency_parties <- names(which(table(voteboard_df$proposedBy_aux)<PARTY_MIN_TRESHOLD))

if(length(low_frequency_parties) > 0) {
  for(i in 1:length(low_frequency_parties)) {
    voteboard_df[voteboard_df[, "proposedBy_aux"] == low_frequency_parties[i],]$proposedBy_aux <- "Outro"
  }
}

########## Calculate probabilities ################################################################################
# Get list of parties  
parties <- unique(as.character(voteboard_df$proposedBy_aux))
print(parties)
# Init parties dataframe
party_probabilities_df <- data.frame(Party=parties, Probab=0)

# Calculate inverse propability for each party
for(i in 1:nrow(party_probabilities_df)) {
  party_probabilities_df[i,]$Probab <- 1 - (nrow(voteboard_df[voteboard_df[, "proposedBy_aux"] == as.character(party_probabilities_df[i,]$Party),])/nrow(voteboard_df))
}

library("DMwR")

# Apply softmax to the probabilities - there should be plenty implementations of this in Python
party_probabilities_df$Probab <- DMwR::SoftMax(party_probabilities_df$Probab,lambda = 4)
# Create a new attribute in the voteboard_df with the respective probabilities for each proposal according to their party
voteboard_df["Probab"] <- party_probabilities_df[match(voteboard_df$proposedBy_aux,party_probabilities_df$Party),]$Probab

head(voteboard_df)

# output_df = voteboard_df[,c("BID","Probab","proposedBy_aux","is_governo")]
# output_df["is_governo"] <- sapply(output_df["is_governo"], as.logical)
write.csv(voteboard_df, file = output_file, quote = FALSE)

# write.csv(voteboard_df, file = "probabilities.csv")

## Testing Sampling.
# Sample 3 proposals for is_governo and 7 that are not
# ids <- c(sample(rownames(voteboard_df[voteboard_df$is_governo=="true",]),3,prob = voteboard_df[voteboard_df$is_governo=="true",]$Probab),
#          sample(rownames(voteboard_df[voteboard_df$is_governo=="false",]),7,prob = voteboard_df[voteboard_df$is_governo=="false",]$Probab))

# vote_sample <- voteboard_df[as.numeric(ids),]
# head(vote_sample)

# head(voteboard_df)