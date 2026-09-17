class Brew2fink < Formula
  desc "Safe Homebrew to Fink migration planner"
  homepage "https://github.com/tomck/brew2fink"
  url "https://github.com/tomck/brew2fink/archive/refs/tags/v0.5.0.tar.gz"
  sha256 "ef9530ee82449f111c7178b675b797c6d7bc5259506d0a49828c6704b32ccc8a"
  license "MIT"
  depends_on "python@3.14"

  def install
    libexec.install "brew2fink"
    (bin/"brew2fink").write <<~EOS
      #!/bin/sh
      export PYTHONPATH="#{libexec}${PYTHONPATH:+:$PYTHONPATH}"
      exec "#{Formula["python@3.14"].opt_bin}/python3.14" -m brew2fink "$@"
    EOS
    chmod 0755, bin/"brew2fink"
  end

  test do
    system bin/"brew2fink", "--help"
  end
end
