class Brew2fink < Formula
  desc "Safe Homebrew to Fink migration planner"
  homepage "https://github.com/tomck/brew2fink"
  url "https://github.com/tomck/brew2fink/archive/refs/tags/v0.7.0.tar.gz"
  sha256 "459fe8e3bc583182cec36901dc46f9eddd37b6f4f04af1756d4fbfa5ac0dd638"
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
