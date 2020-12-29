FROM circleci/android:api-29-node


RUN gem install fastlane -NV
RUN sdkmanager --install \
          "ndk;21.3.6528147" \
          "cmake;3.10.2.4988404"
