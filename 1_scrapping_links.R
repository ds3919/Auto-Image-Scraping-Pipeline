options(repos = c(CRAN = "https://cran.r-project.org"))

# Install required packages
if (!require('rvest')) install.packages('rvest')
if (!require('httr')) install.packages('httr')
if (!require('tidyverse')) install.packages('tidyverse')

library(rvest)
library(httr)
library(tidyverse)
library(xml2)

print(getwd())

# Args: <searchTags> <immutableIndex> <instCount>
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4) {
  stop("Usage: Rscript myscript.R <searchTags> <immutableIndex> <instCount> <wordList>", call. = FALSE)
}

# Rscript myscript.R "photorealistic,256x256,high definition" 2 50 

# User-Agent rotation
user_agents <- c(
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
  "Mozilla/5.0 (X11; Linux x86_64)"
)

random_user_agent <- function() sample(user_agents, 1)

# Safe HTML fetch with retry and exponential backoff
safe_read_html <- function(url, retries = 5, backoff = 2) {
  attempt <- 1
  while (attempt <= retries) {
    tryCatch({
      page <- read_html(GET(url, user_agent(random_user_agent())))
      return(page)
    }, error = function(e) {
      message(sprintf("Attempt %d failed: %s", attempt, e$message))
      Sys.sleep(backoff ^ attempt)
      attempt <<- attempt + 1
    })
  }
  stop(sprintf("Failed to fetch URL after %d retries: %s", retries, url))
}

# Fix Bing image URLs
fix_urls <- function(urls_list) {
  lapply(urls_list, function(url) paste0("https://www.bing.com", url))
}

# Image scraping with progressive tag removal
# get_image_urls <- function(word, tags, immutable_index, max_results) {
#   immutable_tags <- tags[1:immutable_index]
#   mutable_tags <- tags[(immutable_index + 1):length(tags)]
#   collected_urls <- c()
#   immutable_start_time <- NULL
#   current_mutable_tags <- mutable_tags

#   while (length(collected_urls) < max_results) {
#     query <- paste(c(word, immutable_tags, current_mutable_tags), collapse = " ")
#     url <- paste0("https://www.bing.com/images/search?q=", URLencode(query))
#     attempt_start <- Sys.time()

#     urls_found <- tryCatch({
#       webpage <- safe_read_html(url)
#       img_nodes <- html_nodes(webpage, "a[href*='/images/search?']")
#       img_urls <- html_attr(img_nodes, "href")
#       urls_filtrados <- img_urls[grepl("^/images/search\\?view", img_urls)]
#       unlist(fix_urls(urls_filtrados))
#     }, error = function(e) {
#       message("Error fetching: ", e$message)
#       c()
#     })

#     if (length(urls_found) > 0) {
#       collected_urls <- unique(c(collected_urls, urls_found))
#     }

#     elapsed <- as.numeric(difftime(Sys.time(), attempt_start, units = "secs"))

#     if (elapsed > 30 && length(current_mutable_tags) > 0) {
#       message("No results for 30s. Removing lowest priority tag: ", current_mutable_tags[length(current_mutable_tags)])
#       current_mutable_tags <- current_mutable_tags[-length(current_mutable_tags)]
#     } else if (elapsed > 30 && length(current_mutable_tags) == 0) {
#       if (is.null(immutable_start_time)) {
#         immutable_start_time <- Sys.time()
#         message("No mutable tags left. Now scraping with immutable tags only.")
#       }
#       immutable_elapsed <- as.numeric(difftime(Sys.time(), immutable_start_time, units = "mins"))
#       if (immutable_elapsed > 10) {
#         message(sprintf("⚠️ Timeout scraping '%s' after 10 mins with immutable tags. Moving on.", word))
#         break
#       }
#     }

#     Sys.sleep(sample(2:5, 1))
#   }

#   return(collected_urls)
# }

get_image_urls <- function(word, tags, immutable_index, max_results) {
  immutable_tags <- tags[1:immutable_index]
  mutable_tags <- tags[(immutable_index + 1):length(tags)]

  collected_urls <- c()
  immutable_start_time <- NULL
  word_start_time <- Sys.time()  # Start a global timer for the word
  current_mutable_tags <- mutable_tags

  while (length(collected_urls) < max_results) {
    # Global timeout check: stop after 20 minutes total
    word_elapsed <- as.numeric(difftime(Sys.time(), word_start_time, units = "mins"))
    if (word_elapsed > 20) {
      message(sprintf("⚠️ Total timeout scraping '%s' after 20 mins. Moving on.", word))
      break
    }

    # Build the query
    query <- paste(c(word, immutable_tags, current_mutable_tags), collapse = " ")
    url <- paste0("https://www.bing.com/images/search?q=", URLencode(query))
    attempt_start <- Sys.time()

    # Scrape the page
    urls_found <- tryCatch({
      webpage <- safe_read_html(url)
      img_nodes <- html_nodes(webpage, "img.mimg")
      img_urls <- html_attr(img_nodes, "src")
      img_urls <- img_urls[grepl("^https?://", img_urls)]
      img_urls
    }, error = function(e) {
      message("Error fetching: ", e$message)
      c()
    })

    if (length(urls_found) > 0) {
      collected_urls <- unique(c(collected_urls, urls_found))
    }

    elapsed <- as.numeric(difftime(Sys.time(), attempt_start, units = "secs"))

    # Remove mutable tags on stall (>30s no new results)
    if (elapsed > 30 && length(current_mutable_tags) > 0) {
      message("No results for 30s. Removing lowest priority tag: ", current_mutable_tags[length(current_mutable_tags)])
      current_mutable_tags <- current_mutable_tags[-length(current_mutable_tags)]
    } else if (elapsed > 30 && length(current_mutable_tags) == 0) {
      if (is.null(immutable_start_time)) {
        immutable_start_time <- Sys.time()
        message("No mutable tags left. Now scraping with immutable tags only.")
      }
      immutable_elapsed <- as.numeric(difftime(Sys.time(), immutable_start_time, units = "mins"))
      if (immutable_elapsed > 10) {
        message(sprintf("⚠️ Timeout scraping '%s' after 10 mins with immutable tags. Moving on.", word))
        break
      }
    }

    Sys.sleep(sample(2:5, 1))
  }

  return(collected_urls[1:min(length(collected_urls), max_results)])
}



# ----- Load Word List -----
words <- read.csv(file.path(args[4]), header = TRUE, fileEncoding = "Latin1")
english <- words$English.Gloss

# ----- Load Previously Saved Results -----
results_file <- "image_results.csv"
if (file.exists(results_file)) {
  message("⚙️ Resuming from existing results.")
  existing_results <- read.csv(results_file, fileEncoding = "Latin1", stringsAsFactors = FALSE)
  scraped_words <- unique(existing_results$word)
} else {
  message("⚙️ Starting fresh scrape.")
  scraped_words <- c()
}

# ----- Parse Tags -----
tags <- strsplit(args[1], ",")[[1]]
immutable_index <- as.integer(args[2])
max_results <- as.integer(args[3])

# ----- Start Scraping -----
for (word in english) {
  if (word %in% scraped_words) {
    message(sprintf("✔️ Word '%s' already scraped. Skipping.", word))
    next
  }

  message(sprintf("🔍 Scraping word: '%s'", word))
  image_urls <- get_image_urls(word, tags, immutable_index, max_results)

  if (length(image_urls) > 0) {
    result_df <- data.frame(word = word, urls = image_urls, timestamp = Sys.time(), stringsAsFactors = FALSE)
    write.table(result_df, results_file, sep = ",", row.names = FALSE, col.names = !file.exists(results_file), append = file.exists(results_file), fileEncoding = "Latin1")
  } else {
    message(sprintf("⚠️ No images found for '%s'", word))
  }

  Sys.sleep(sample(5:10, 1))
}

# ----- Final Deduplication -----
message("✅ Final deduplication and save.")
final_results <- read.csv(results_file, fileEncoding = "Latin1", stringsAsFactors = FALSE)
final_results_unique <- final_results %>% distinct(urls, .keep_all = TRUE)
write.csv(final_results_unique, results_file, row.names = FALSE, fileEncoding = "Latin1")

message("🎉 Scraping complete.")
