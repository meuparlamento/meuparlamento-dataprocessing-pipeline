#!/usr/bin/env Rscript
args = commandArgs(trailingOnly=TRUE)

# test if there is at least one argument: if not, return an error
if (length(args)==0) {
  stop("At least one argument must be supplied (link to pdf)", call.=FALSE)
} 

## program...
library(pdftools)
library(stringr)

doc <- pdftools::pdf_text(args[1])

newdoc <- list()

npages <- length(doc)

for(p in 1:npages) {
  
  pg <- doc[p]
  
  snts <- unlist(strsplit(pg,"[\\.;:]\n"))
  
  new_snts <- unlist(lapply(snts, FUN=function(x) {
    
    if(grepl("^\\s", x)) {
      aux <- substr(x,gregexpr(pattern = "\\n\\w.+",x)[[1]][1],nchar(x))
      aux <- gsub("\\d\n$", " ", aux)
      aux <- gsub("\n", " ", aux)
      aux <- trimws(aux)
      aux <- gsub("\\s\\s+"," ",aux)
      aux
      
    } else {
      
      aux <- gsub("\\d\n$", " ", x)
      aux <- gsub("\n", " ", aux)
      aux <- trimws(aux)
      aux <- gsub("\\s\\s+"," ",aux)
      aux
      
    }
  }))
  
  newdoc <- c(newdoc,new_snts)
  
}

newdoc <- unlist(newdoc)

for(i in 1:length(newdoc)) {
  
  newdoc[i] = gsub(".+Exposição de motivos.+", "", newdoc[i])
  newdoc[i] = gsub(".+Exposição de Motivos.+", "", newdoc[i])
  newdoc[i] = gsub("^Projeto.+", "", newdoc[i])
  newdoc[i] = gsub("^Projecto.+", "", newdoc[i])
  newdoc[i] = gsub("^PROJETO.+", "", newdoc[i])
  newdoc[i] = gsub("^PROJECTO.+", "", newdoc[i])
  newdoc[i] = gsub("Email: \\S+@\\S+\\.\\S+", "", newdoc[i])
  newdoc[i] = gsub("Telefone:(\\s|\\d)+", "", newdoc[i])
  newdoc[i] = gsub('Fax:(\\s|\\d)+', "", newdoc[i])
  newdoc[i] = gsub('Assembleia da Rep.blica . Pal.cio de S\\. Bento . 1249.068 Lisboa', "", newdoc[i])
  newdoc[i] = gsub('Assembleia da República, \\d+.+$', "", newdoc[i])
  newdoc[i] = gsub('(ftp|http|https):\\/\\/[^ "]+', "", newdoc[i])
  newdoc[i] = gsub('^Pal.cio de São Bento.+', "[...]", newdoc[i])
  newdoc[i] = gsub('Grupo Parlamentar do Bloco de Esquerda', "[...]", newdoc[i])
  newdoc[i] = gsub('(- )+', "", newdoc[i])
  newdoc[i] = gsub('(– )+', "", newdoc[i])
  newdoc[i] = gsub('PARTIDO COMUNISTA PORTUGU.S', "[...]", newdoc[i])
  newdoc[i] = gsub('Partido Socialista', "[...]", newdoc[i])
  newdoc[i] = gsub('Grupo Parlamentar do PCP', "[...]", newdoc[i])
  newdoc[i] = gsub('Grupo Parlamentar do Partido Social Democrata', "[...]", newdoc[i])
  newdoc[i] = gsub('Grupo Parlamentar do PSD', "[...]", newdoc[i])
  newdoc[i] = gsub('Os Deputados, .+$', "[...]", newdoc[i])
  newdoc[i] = gsub('Grupo Parlamentar Os Verdes', "[...]", newdoc[i])
  newdoc[i] = gsub('Grupo Parlamentar do Partido Socialista', "[...]", newdoc[i])
  newdoc[i] = gsub('Grupo Parlamentar do PS', "[...]", newdoc[i])
  newdoc[i] = gsub('Grupo Parlamentar do CDS.PP', "[...]", newdoc[i])
  newdoc[i] = gsub('Bloco de Esquerda', "[...]", newdoc[i])
  newdoc[i] = gsub('PS, PSD e CDS', "[...]", newdoc[i])
  newdoc[i] = gsub('PSD\\/CDS.PP', "[...]", newdoc[i])
  newdoc[i] = gsub('PSD\\/CDS', "[...]", newdoc[i])
  newdoc[i] = gsub('Grupo Parlamentar', "[...]", newdoc[i])
  newdoc[i] = gsub('Governo PSD-CDS', "[...]", newdoc[i])
  newdoc[i] = gsub('Governo PS', "[...]", newdoc[i])
  newdoc[i] = gsub('PSD', "[...]", newdoc[i])
  newdoc[i] = gsub('PCP', "[...]", newdoc[i])
  newdoc[i] = gsub('PS', "[...]", newdoc[i])
  newdoc[i] = gsub('CDS.PP', "[...]", newdoc[i])
  newdoc[i] = gsub('CDS', "[...]", newdoc[i])
  newdoc[i] = gsub('PEV', "[...]", newdoc[i])
  newdoc[i] = gsub('PAN', "[...]", newdoc[i])
  newdoc[i] = gsub('(Os|As) (Deputados|Deputadas) [A-ZÁÀÃÂÉÈÊÍÌÎÓÒÕÔÚÙÛÇ’\\-\\s]+$', "[...]", newdoc[i])
  newdoc[i] = gsub('Partido Ecologista Os (V|v)erdes (PEV)', "[...]", newdoc[i])
  newdoc[i] = gsub('Partido Ecologista Os (V|v)erdes', "[...]", newdoc[i])
  newdoc[i] = gsub('Os Verdes', "[...]", newdoc[i])
  newdoc[i] = gsub('^[…]\\s', "", newdoc[i])
  newdoc[i] = gsub('^', "-", newdoc[i])
  newdoc[i] = gsub('^\\d(\\s|\\.)+', "", newdoc[i])
  
  newdoc[i] = gsub('(\\(.+\\))\\s+(\\(.+\\))', "[...]", newdoc[i])
  
}

rmv <- c()
brk <- c()
brk2 <- c()

for(i in 1:length(newdoc)) {
  
  if(str_count(newdoc[i],'\\w+')<6) {
    rmv <- c(rmv,i)
  }
  
  if(grepl("^[a-záàãâóòôõéèêíìîúùû]",newdoc[i])) {
    brk <- c(brk,i)
    newdoc[i-1] <- paste0(newdoc[i-1]," ",newdoc[i])
  }
  
  if(grepl("\\s$",newdoc[i])) {
    brk2 <- c(brk2,i)
    newdoc[i+1] <- paste0(newdoc[i]," ",newdoc[i+1])
  }
}

newdoc_aux = tryCatch(
        {
          newdoc_aux <- newdoc[-c(rmv,brk,brk2)]
        },
        error=function(cond) {}
)

if(!is.null(newdoc_aux)){
  newdoc = newdoc_aux
}

newdoc <- unlist(lapply(newdoc,FUN=function(x) {
  x_aux <- paste0(x,".")
  gsub("\\s+", " ", str_trim(x_aux))
})  )

newdoc <- newdoc[-length(newdoc)]

##### TEXTRANK

library(lexRankr)

top_sentences <- lexRankr::lexRank(newdoc,
                                   #only 1 article; repeat same docid for all of input vector
                                   docId = rep(1, length(newdoc)),
                                   n = 10,
                                   continuous = TRUE,
                                   removePunc=FALSE,
                                   removeNum = FALSE,
                                   Verbose=FALSE)

order_of_appearance <- order(as.integer(gsub("_","",top_sentences$sentenceId)))
ordered_top <- top_sentences[order_of_appearance, "sentence"]
#ordered_top

tot <- 0
i <- 0
include_stns <- c()
while(i<10) {
  if(tot + nchar(ordered_top[i+1])<1000) {
    if(nchar(ordered_top[i+1])>10) {
      i <- i + 1; tot <- tot + nchar(ordered_top[i]); include_stns <- c(include_stns,i) 
    } else {
      i <- i + 1
    }
    
  } else
    break
}

ordered_top <- ordered_top[include_stns]

if(length(ordered_top)==0) {
  top_sentences <- lexRankr::lexRank(newdoc,
                                     #only 1 article; repeat same docid for all of input vector
                                     docId = rep(1, length(newdoc)),
                                     n = 50,
                                     continuous = TRUE,
                                     removePunc=FALSE,
                                     removeNum = FALSE,
                                     Verbose=FALSE)
  
  order_of_appearance <- order(as.integer(gsub("_","",top_sentences$sentenceId)))
  ordered_top <- top_sentences[order_of_appearance, "sentence"]
  #ordered_top
  
  tot <- 0
  i <- 0
  include_stns <- c()
  while(i<10) {
    if(tot + nchar(ordered_top[i+1])<1000) {
      if(nchar(ordered_top[i+1])>10) {
        i <- i + 1; tot <- tot + nchar(ordered_top[i]); include_stns <- c(include_stns,i) 
      } else {
        i <- i + 1
      }
      
    } else
      break
  }
  
  ordered_top <- ordered_top[include_stns]
}

paste(ordered_top, collapse="\n")
