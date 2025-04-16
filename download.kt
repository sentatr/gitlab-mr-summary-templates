import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File

fun downloadFile(projectId: String, filePath: String, branch: String, outputFile: String) {
    val client = OkHttpClient()
    val jobToken = System.getenv("CI_JOB_TOKEN") ?: error("CI_JOB_TOKEN not found")
    val url = "https://gitlab.com/api/v4/projects/$projectId/repository/files/$filePath/raw?ref=$branch"

    val request = Request.Builder()
        .url(url)
        .header("PRIVATE-TOKEN", jobToken)
        .build()

    client.newCall(request).execute().use { response ->
        if (response.isSuccessful) {
            File(outputFile).writeBytes(response.body!!.bytes())
            println("File downloaded: $outputFile")
        } else {
            error("Failed to download file: ${response.code}")
        }
    }
}


build.gradle.kts

tasks.register("fetchGitLabFile") {
    doLast {
        downloadFile("123456", "path/to/file.txt", "main", "localFile.txt")
    }
}

yml:

stages:
  - download

download_file:
  stage: download
  script:
    - ./gradlew fetchGitLabFile
